<div align="center">

<img width="2743" height="872" alt="Frame 13 (3)" src="https://github.com/user-attachments/assets/e1ee2932-d7c0-45e6-a5f1-f9e6e41f4f7d" />


# ThreatIQ

### We built AI fraudsters to train a better fraud detector

**Mastercard Innovation Challenge 2026 · AI Defense Lab for Payment Security**

[![Live Demo](https://img.shields.io/badge/Live_Demo-iqthreat.vercel.app-F37338?style=for-the-badge&logo=vercel&logoColor=white)](https://iqthreat.vercel.app)
[![API](https://img.shields.io/badge/Live_API-Swagger_Docs-10B981?style=for-the-badge&logo=fastapi&logoColor=white)](https://backend-production-400c.up.railway.app/docs)
[![Tests](https://img.shields.io/badge/tests-42_passing-0A8150?style=for-the-badge)](tests/)
[![Validated](https://img.shields.io/badge/validated_on-284,807_real_payments-2F5FB3?style=for-the-badge)](#we-checked-our-work-on-real-fraud)

</div>

---

Criminals now use AI to commit payment fraud, which makes it faster to produce and much harder to spot. **ThreatIQ fights back by doing both jobs at once.** It builds AI attackers that invent new ways to steal, and an AI defender that learns to catch them. The two are wired together, so every time the attackers find a trick that works, the defender learns from it.

Partway through building this, we discovered our own test was too easy, and that our "we catch 100% of fraud" result was meaningless. We rebuilt it honestly, then checked our work against **284,807 real credit card payments**.

<div align="center">

| Catches | Of its alerts | Beats a one line rule by | Validated on |
|:--:|:--:|:--:|:--:|
| **75%** of real fraud | **81%** are genuine | **+0.283** F1 | **284,807** real payments |

</div>

---

## The mistake we caught, and why it matters
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_51_23 PM" src="https://github.com/user-attachments/assets/31884c94-6acd-455b-a4f4-0710c76aef0c" />


<!-- ══ IMAGE 2 · BENCHMARK VALIDITY CHART ══════════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 2"
     Save as:  docs/images/02-test-too-easy.png        (16:9)
<img src="docs/images/02-test-too-easy.png" alt="Our old test could be solved by a single rule" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

To test a fraud detector you need example payments, some fake and some normal. We wrote a program to create them. Without meaning to, we made the fake ones obviously different: every fake payment scored between 0.10 and 0.40 on a "how human does this seem" measure, and every normal one scored between 0.70 and 0.99. **The two never overlapped**, so a single line of code separated them perfectly.

Our system was not catching fraud. It was reading a clue we had accidentally left in the data. A perfect score was proof our test was broken, not that our system was good.

We rebuilt how we create fake payments, copying how fraud actually behaves. Now the same test says:

| Detector | Accuracy (F1) | Of its alerts, how many are real fraud | How much fraud it catches | False alarm rate |
|---|:--:|:--:|:--:|:--:|
| One simple rule | 0.583 | 46% | 79% | 16.2% |
| Simplest possible model | 0.584 | 46% | 79% | 16.1% |
| **Our full system** | **0.867** | **89%** | **85%** | **1.9%** |

We also made this impossible to repeat quietly. The benchmark prints the simple rule's score next to ours **on every run**, and an automated test fails the whole project if a one line rule ever gets close again.

---

## We checked our work on real fraud
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_53_09 PM" src="https://github.com/user-attachments/assets/b2981d51-84d0-41e7-b0bf-0e192ae28d18" />


<!-- ══ IMAGE 3 · REAL DATA ALERT BUDGET CURVE ══════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 3"
     Save as:  docs/images/03-real-data.png            (16:9)
<img src="docs/images/03-real-data.png" alt="Tested on 284,807 real payments" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

A test you write yourself can be made to say whatever you want. So we tested against **284,807 real credit card payments** containing **492 genuine frauds**, training on earlier payments and testing on later ones, the way it would work in real life.

A fraud team can only investigate so many alerts per day, so the honest question is what you get for a given amount of staff time:

| Alerts to review per day | Fraud caught | Alerts that are real fraud | Staff for 1 million payments a day |
|:--:|:--:|:--:|:--:|
| **100** | **75%** | **81%** | **about 5 people** |
| 400 | 79% | 21% | about 20 people |
| 1,600 | 83% | 6% | about 78 people |

Five staff catching three quarters of all fraud, with four out of five alerts genuine, is a workable setup for a real bank.

> This exercise also found a real bug in our own code. One function was throwing away the results of our best model before making a decision. Fixing it more than doubled real world performance.

---

## Why it matters how rare fraud is
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_54_04 PM" src="https://github.com/user-attachments/assets/ad62fa0d-1a42-4390-a36c-791eecdf16c7" />


<!-- ══ IMAGE 4 · PRECISION VS PREVALENCE CURVE ═════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 4"
     Save as:  docs/images/04-rare-fraud.png           (16:9)
<img src="docs/images/04-rare-fraud.png" alt="Accuracy depends on how rare fraud is" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

In our own test, about 15 in every 100 payments were fraud. In the real world it is closer to **2 in every 1,000**. That changes everything, even though the detector does not change at all.

| If this share of payments is fraud | Then this share of alerts are real | False alarms per real catch |
|:--:|:--:|:--:|
| 15 in 100 (our test) | 89% | 0.1 |
| 1 in 100 | 31% | 2.2 |
| **2 in 1,000 (real world)** | **7%** | **13** |

When something is rare, even a small false alarm rate produces far more false alarms than real catches. This is why we publish the alert budget table instead of one impressive number, and why we always state how common fraud was in any test we report.

---

## How it works

<!-- ══ IMAGE 5 · THE FOUR STAGE LOOP DIAGRAM ═══════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 5"
     Save as:  docs/images/05-loop.png                 (3:1)
<img src="docs/images/05-loop.png" alt="Find, recreate, catch, learn" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

<div align="center">

**Find the attacks → Recreate them realistically → Catch them → Learn and repeat**

</div>

### 1. Find

Six new ways criminals use AI against payments, across eight categories, each mapped to a recognised industry catalogue of AI attacks and to the exact fields in the standard messages banks send each other.

| Code | The attack | What the criminal does | Severity |
|---|---|---|:--:|
| `ATK-001` | Fake identities built by AI | Invents people who do not exist, with believable credit histories | Critical |
| `ATK-002` | Automated shopping bots | Buys goods with stolen cards through hundreds of connections | Critical |
| `ATK-003` | Tricking a shop's AI assistant | Hidden instructions to change payment details or leak card data | High |
| `ATK-004` | Cloned voices | Copies a voice from seconds of public audio to beat phone security | High |
| `ATK-005` | Checkout loopholes | Exploits timing gaps to get goods without a valid payment | High |
| `ATK-006` | Learning the limits | Works out a bank's spending limits, then stays just underneath | Medium |

### 2. Recreate
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_56_16 PM" src="https://github.com/user-attachments/assets/8cd958a6-9fac-4c65-a13e-523af08b2e7d" />


<!-- ══ IMAGE 6 · THE THREE ATTACKER TYPES ══════════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 6"
     Save as:  docs/images/06-attacker-types.png       (12:5)
<img src="docs/images/06-attacker-types.png" alt="Three types of attacker, the skilled one blending in" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

**Not all criminals are equally good.** Most fraud is clumsy. A small amount is done by skilled operators who work hard to look exactly like a normal customer. A test containing only clumsy fraud makes any detector look brilliant, then fails in production.

| Type | Share of fraud | How human they seem | Amounts | Time of day |
|---|:--:|:--:|---|---|
| Clumsy | 45% | 0.10 to 0.45 | Much larger | Odd hours |
| Average | 35% | 0.35 to 0.72 | Slightly larger | Mixed |
| **Skilled** | 20% | **0.58 to 0.96** | Normal | **Normal shopping hours** |


<!-- ══ IMAGE 7 · RECALL BY ATTACKER SKILL CHART ════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 7"
     Save as:  docs/images/07-attacker-skill.png       (16:9)
<img src="docs/images/07-attacker-skill.png" alt="How much fraud we catch, by attacker skill" width="100%" />
════════════════════════════════════════════════════════════════════════ -->
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_57_05 PM" src="https://github.com/user-attachments/assets/5ed683c5-a03d-408f-8703-54446e5e87a5" />


Real customers score 0.30 to 0.99, so skilled attackers sit almost completely inside the normal range. **We catch 98% of clumsy fraud and only 50% of skilled fraud.** We put that front and centre rather than hiding it. AI has not mainly made fraud more common, it has made *looking like a normal customer* cheap.

Our normal customers are realistically awkward too: 18 in 100 score low for innocent reasons, 6 in 100 make an unusually large purchase, and 5 in 100 are travelling abroad.

<!-- ══ IMAGE 8 · FRAUD GANGS SHARING EQUIPMENT ═════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 8"
     Save as:  docs/images/08-gangs.png                (16:9)
<img src="docs/images/08-gangs.png" alt="Fraud gangs sharing equipment" width="100%" />
════════════════════════════════════════════════════════════════════════ -->

Criminals share equipment, with 60% of fake fraud belonging to one of twelve gangs that reuse devices, card ranges and connections. This gives our gang detection something real to find.

### 3. Catch

| Model | Good at | Quality on real data |
|---|---|:--:|
| **XGBoost** | Learning patterns from labelled examples | Excellent |
| **LightGBM** | A second opinion | Good |
| **Isolation Forest** | Spotting anything unusual | Fair |
| Network model | Spotting fraud gangs | **Not trained, switched off** |

We list the fourth honestly. It is built but untrained and disabled, so it contributes nothing to any number here. We would rather say so than have someone find it in the code.

---

## The two sides really are connected

<!-- ══ IMAGE 9 · ATTACKER BOTS LEARNING CURVE ══════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 9"
     Save as:  docs/images/09-bots-learning.png        (16:9)
<img src="docs/images/09-bots-learning.png" alt="The attacker bots really do learn" width="100%" />
════════════════════════════════════════════════════════════════════════ -->
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 08_59_25 PM" src="https://github.com/user-attachments/assets/1138c629-0fe4-4194-bef4-ecc5fd1112c7" />


When you press "run a training round" in the app:

1. Each of six attacker bots picks a strategy
2. That strategy creates new fraudulent payments
3. Those go through **the real, live detector**
4. Whatever the detector actually caught becomes the bot's score
5. The bot updates its strategy from that score

The bots keep what worked and build on it. One thing they can invest in is **imitating human behaviour**, exactly the ability AI has made cheap for real criminals. Over 60 rounds, attacks getting through rise from about 29% to over 85%.

> An earlier version of our app faked this. The chart moved upward using random numbers, ignoring what the system reported. We removed it. A demonstration that cannot fail proves nothing.

---

## Keeping it safe in the real world

<!-- ══ IMAGE 10 · FRAUD PATTERNS DRIFTING ══════════════════════════════════
     Prompt:   docs/IMAGE_PROMPTS.md  →  "Image 10"
     Save as:  docs/images/10-drift.png                (16:9)
<img src="docs/images/10-drift.png" alt="Fraud patterns change within 48 hours" width="100%" />
════════════════════════════════════════════════════════════════════════ -->
<img width="1536" height="1024" alt="ChatGPT Image Aug 31, 2026, 09_00_24 PM" src="https://github.com/user-attachments/assets/bed41d81-ea1b-4d99-9666-cd4233403afb" />


Real data shows a detector that is never updated gets noticeably worse **within two days**. But updating a live detector is dangerous, and we learned this the hard way: one unguarded retraining run using 20 examples took the share of genuine alerts from **86% down to 24%**.

So we added a safety gate, the same idea a real bank would use:

1. At least 400 examples, including both fraud and normal payments
2. The new model trains as a **candidate**, and the live one is never touched
3. Both are tested on data neither has seen
4. The candidate replaces the live model **only if it is genuinely better**

After the gate: 88% fraud caught, 85% of alerts genuine, matching our offline results instead of drifting from them.

---

## Try it yourself

```bash
git clone https://github.com/prerak09/ThreatIQ.git && cd ThreatIQ
pip install -r requirements.txt

# Regenerate every number in this README
python benchmark.py --seed 42

# Run the full test suite
python -m pytest tests/ -q
```

Then start the app:

```bash
uvicorn src.api.app:app --reload --port 8000    # backend on :8000
cd dashboard && npm install && npm run dev      # dashboard on :3000
```

<!-- ══ IMAGE 11 · DASHBOARD SCREENSHOT ═════════════════════════════════════
     This one is a SCREENSHOT, not generated. Capture instructions in
     docs/IMAGE_PROMPTS.md  →  "Image 11"
     Save as:  docs/images/11-dashboard.png
<img src="docs/images/11-dashboard.png" alt="The ThreatIQ dashboard" width="100%" />
════════════════════════════════════════════════════════════════════════ -->
<img width="1162" height="423" alt="image" src="https://github.com/user-attachments/assets/36a7f72e-5379-4d69-b9b0-a4e4ee749b95" />

---

## Our tests are not decoration

Each one guards against a specific way this project could quietly become dishonest.

| Test file | What it stops from happening |
|---|---|
| `test_generator_integrity.py` | Our fake fraud becoming too easy to spot again |
| `test_marl_learning.py` | The attacker bots quietly stopping learning while still drawing a nice chart |
| `test_zkp_soundness.py` | Our verification accepting a fake or tampered proof |
| `test_api_contract.py` | Bad input reaching the detector, or one request crashing the service |

---

## What we would build next

| Area | Today | Next |
|---|---|---|
| Proof of correct screening | Simpler cryptography that proves the check ran untampered | A full zero knowledge proof system, which the code is structured for |
| Gang detection | Finds groups sharing equipment | Train the network model we built but have not trained |
| Combining models | Fixed weights | Better weighting, which real data shows would improve results |
| Creating fake payments | Follows hard rules on amounts and limits | Train it on real payment patterns too |
| Bank to bank learning | Simulated on one machine, privacy maths done properly | A real deployment across multiple banks |
| Speed | About 30 ms per single payment | Under 15 ms, by moving one slow step off the main path |

---

## Repository layout

```
src/
  threat_intel/      Attack taxonomy, industry mappings, message field mappings
  red_team/          Attacker and customer simulation, attacker bots, message formatting
  blue_team/         Detection models, explanations, safe retraining, gang detection
  api/               FastAPI service, 41 endpoints and a live stream
dashboard/           Next.js dashboard, 11 screens
tests/               42 tests
benchmark.py         Regenerates every published number
docs/IMAGE_PROMPTS.md  Prompts for every image in this README
```

---

<div align="center">

### Team ThreatIQ

**Prerak Tanwar** · **Vishakha Sanjay Yadav**

<sub>Our own test results come from <code>benchmark.py --seed 42</code>, using 12,000 payments to train and 6,000 to test at 15% fraud. Real world results come from a public dataset of 284,807 credit card payments containing 492 frauds, trained on the first 70% of the time period and tested on the last 30%.</sub>

</div>
