"""TabDDPM: Tabular Denoising Diffusion Probabilistic Model for synthetic transaction generation."""

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def gaussian_noise_schedule(timesteps, beta_start=1e-4, beta_end=0.02):
    betas = np.linspace(beta_start, beta_end, timesteps)
    alphas = 1.0 - betas
    alphas_cumprod = np.cumprod(alphas)
    return betas, alphas, alphas_cumprod


def enforce_benford_first_digits(amounts):
    """Adjust transaction amounts so their leading digits follow Benford's law.

    Magnitudes (decades) are preserved; only the leading digit of each
    amount is reassigned so the digit histogram matches P(d) = log10(1+1/d).
    """
    amounts = np.asarray(amounts, dtype=np.float64).copy()
    n = amounts.size
    if n == 0:
        return amounts
    signs = np.sign(amounts)
    mags = np.abs(amounts)
    mags[mags < 1e-9] = 1e-9
    exponents = np.floor(np.log10(mags)).astype(int)

    benford = np.log10(1.0 + 1.0 / np.arange(1, 10))
    target_counts = np.floor(benford * n).astype(int)
    deficit = n - int(target_counts.sum())
    for _ in range(deficit):  # distribute rounding leftovers
        target_counts[int(np.argmax(target_counts - benford * n))] += 1

    target_digits = np.concatenate(
        [np.full(c, d + 1, dtype=int) for d, c in enumerate(target_counts)]
    )
    np.random.shuffle(target_digits)

    fracs = np.random.uniform(0.0, 1.0, size=n)
    new_mags = target_digits * (10.0 ** exponents) + fracs * (10.0 ** exponents)
    return signs * new_mags


class ConditionalDenoisingScoreMatching:
    def __init__(self, feature_dim, noise_schedule):
        self.feature_dim = feature_dim
        self.betas, self.alphas, self.alphas_cumprod = noise_schedule

    def compute_loss(self, x_0, noise, t):
        alpha_t = self.alphas_cumprod[t]
        x_t = np.sqrt(alpha_t) * x_0 + np.sqrt(1 - alpha_t) * noise
        return np.mean((noise - x_t) ** 2)


if TORCH_AVAILABLE:
    class TabDDPM(nn.Module):
        def __init__(self, feature_dim, hidden_dim=256, num_timesteps=100,
                     beta_start=1e-4, beta_end=0.02):
            super().__init__()
            self.feature_dim = feature_dim
            self.num_timesteps = num_timesteps
            betas, _, _ = gaussian_noise_schedule(num_timesteps, beta_start, beta_end)
            betas_t = torch.tensor(betas, dtype=torch.float32)
            alphas = 1.0 - betas_t
            self.register_buffer("betas", betas_t)
            self.register_buffer("alphas", alphas)
            self.register_buffer("alphas_cumprod", torch.cumprod(alphas, dim=0))
            self._build_network(hidden_dim)

        def _build_network(self, hidden_dim):
            self.time_embed = nn.Sequential(
                nn.Linear(1, hidden_dim), nn.SiLU(), nn.Linear(hidden_dim, hidden_dim)
            )
            self.denoiser = nn.Sequential(
                nn.Linear(self.feature_dim + hidden_dim, hidden_dim),
                nn.GroupNorm(8, hidden_dim), nn.SiLU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.GroupNorm(8, hidden_dim), nn.SiLU(),
                nn.Linear(hidden_dim, hidden_dim), nn.SiLU(),
                nn.Linear(hidden_dim, self.feature_dim),
            )

        def _time_embedding(self, t: int, n_samples: int, device):
            t_emb = self.time_embed(torch.tensor([[float(t)]], device=device))
            return t_emb.expand(n_samples, -1)

        def forward_diffusion(self, x_0, t):
            noise = torch.randn_like(x_0)
            a = self.alphas_cumprod[t].view(-1, 1).to(x_0.device).sqrt()
            b = (1.0 - self.alphas_cumprod[t]).clamp_min(0.0).view(-1, 1).to(x_0.device).sqrt()
            return a * x_0 + b * noise, noise

        def denoise_step(self, x_t, t, t_next):
            """Single DDPM posterior-mean reverse step."""
            with torch.no_grad():
                inp = torch.cat([x_t, self._time_embedding(t, x_t.shape[0], x_t.device)], dim=-1)
                pred_noise = self.denoiser(inp)
            alpha_t = self.alphas[t]
            beta_t = self.betas[t]
            abar_t = self.alphas_cumprod[t]
            mean = (x_t - (beta_t / (1.0 - abar_t).sqrt()) * pred_noise) / alpha_t.sqrt()
            if t > 0:
                z = torch.randn_like(x_t)
                sigma = beta_t.sqrt()
                return mean + sigma * z
            return mean

        def sample(self, n_samples):
            """Full reverse diffusion from pure noise using DDPM updates."""
            self.eval()
            device = next(self.parameters()).device
            x = torch.randn(n_samples, self.feature_dim, device=device)
            with torch.no_grad():
                for t in range(self.num_timesteps - 1, -1, -1):
                    inp = torch.cat([x, self._time_embedding(t, n_samples, device)], dim=-1)
                    pred_noise = self.denoiser(inp)
                    alpha_t = self.alphas[t]
                    beta_t = self.betas[t]
                    abar_t = self.alphas_cumprod[t]
                    # Standard DDPM posterior step
                    x = (x - (beta_t / (1.0 - abar_t).sqrt()) * pred_noise) / alpha_t.sqrt()
                    if t > 0:
                        sigma = beta_t.sqrt()
                        x = x + sigma * torch.randn_like(x)
            self.train()
            return x.detach().cpu().numpy()

        def train_step(self, x_batch):
            t = torch.randint(0, self.num_timesteps, (x_batch.shape[0],))
            noise = torch.randn_like(x_batch)
            a = self.alphas_cumprod[t].view(-1, 1).sqrt()
            b = (1.0 - self.alphas_cumprod[t]).clamp_min(0.0).view(-1, 1).sqrt()
            x_t = a * x_batch + b * noise
            t_emb = self.time_embed(t.view(-1, 1).float())
            inp = torch.cat([x_t, t_emb], dim=-1)
            return F.mse_loss(self.denoiser(inp), noise).item()

        def fit(self, X, y=None, epochs=100, batch_size=256):
            optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
            X_t = torch.tensor(X, dtype=torch.float32) if not isinstance(X, torch.Tensor) else X
            device = next(self.parameters()).device
            X_t = X_t.to(device)
            for _ in range(epochs):
                perm = torch.randperm(X_t.shape[0])
                for i in range(0, X_t.shape[0], batch_size):
                    batch = X_t[perm[i:i + batch_size]]
                    t = torch.randint(0, self.num_timesteps, (batch.shape[0],), device=device)
                    noise = torch.randn_like(batch)
                    a = self.alphas_cumprod[t].view(-1, 1).sqrt()
                    b = (1.0 - self.alphas_cumprod[t]).clamp_min(0.0).view(-1, 1).sqrt()
                    x_t = a * batch + b * noise
                    t_emb = self.time_embed(t.view(-1, 1).float())
                    inp = torch.cat([x_t, t_emb], dim=-1)
                    loss = F.mse_loss(self.denoiser(inp), noise)
                    optimizer.zero_grad()
                    loss.backward()
                    optimizer.step()

        def generate_fraud_samples(self, n_samples, attack_type="account_takeover"):
            samples = self.sample(n_samples)
            amt_scale = {"account_takeover": 2000, "card_testing": 10,
                         "synthetic_id": 500, "loyalty_fraud": 150}
            samples[:, 0] = np.abs(samples[:, 0]) * amt_scale.get(attack_type, 300)
            samples[:, 0] = enforce_benford_first_digits(samples[:, 0])
            return samples

else:
    class TabDDPM:
        """NumPy stub used when PyTorch is unavailable (no real denoising)."""

        def __init__(self, feature_dim, hidden_dim=256, num_timesteps=100,
                     beta_start=1e-4, beta_end=0.02):
            self.feature_dim = feature_dim
            self.num_timesteps = num_timesteps
            self.betas, self.alphas, self.alphas_cumprod = gaussian_noise_schedule(
                num_timesteps, beta_start, beta_end
            )

        def forward_diffusion(self, x_0, t):
            noise = np.random.randn(*x_0.shape)
            a = np.sqrt(self.alphas_cumprod[t])
            b = np.sqrt(max(0.0, 1.0 - self.alphas_cumprod[t]))
            return a * x_0 + b * noise, noise

        def denoise_step(self, x_t, t, t_next):
            # Without a trained network there is nothing to denoise with.
            return x_t * 0.98

        def sample(self, n_samples):
            return np.random.randn(n_samples, self.feature_dim) * 0.5

        def train_step(self, x_batch):
            return float(np.random.rand())

        def fit(self, X, y=None, epochs=100, batch_size=256):
            pass

        def generate_fraud_samples(self, n_samples, attack_type="account_takeover"):
            samples = np.abs(np.random.randn(n_samples, self.feature_dim))
            amt_scale = {"account_takeover": 2000, "card_testing": 10,
                         "synthetic_id": 500, "loyalty_fraud": 150}
            samples[:, 0] *= amt_scale.get(attack_type, 300)
            samples[:, 0] = enforce_benford_first_digits(samples[:, 0])
            return samples
