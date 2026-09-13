# AI Bootcamp — Foundations of AI

Repository contains the course materials of the AI Bootcamp - Foundations of AI, one week course held by [LARES](https://www.lares.fer.hr/lares), [Faculty of Electrical Engineering and Computing](https://www.fer.unizg.hr/en?), University of Zagreb.

Everything runs in **Google Colab**, in your browser. Nothing to install, no
GPU needed, no credit card. Data and notebooks are fetched automatically from
this repository.

---

## At the beginning of the course (cca. 10 minutes)

> **Use a personal Google account (`@gmail.com`), not a corporate one.**
> Managed Google Workspace accounts frequently have Colab or Google AI Studio
> blocked by an administrator, and that is not something we can usually fix in the duration of the course.

### 1. Check that Colab works

Open [**0_Test**](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/0_Test.ipynb),
sign in if prompted, and run the **first cell**. If it prints `data ok: True`,
everything works and you can close the tab.

**Do not request a GPU runtime.** The entire course runs on CPU. Free GPU quota
is limited and shared, and spending it changes nothing except that it will not
be there when we might actually need it for code execution.

### 2. Create a Gemini API key

Needed on day 4, for the language model and agent sessions. Create it now so
that any account problem surfaces while there is still time. Free, no payment
method required.

1. Open [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Click **Create API key** and copy the result somewhere safe
3. If a project picker appears, choose any project or create a new one — it
   does not matter which

**Everyone needs their own key.** We do not share one, because the daily and
per-minute quotas are counted per account.

### 3. Store the key in Colab

Never paste an API key into a notebook cell. Colab has a dedicated place for
secrets.

1. In Colab, click the **key icon** in the left sidebar (Secrets)
2. **Add new secret** — name `GOOGLE_API_KEY`, value = your key
3. Turn on **Notebook access**

The notebooks read it from there. It never appears in the code, and it never
travels to GitHub with a saved copy.

**If any of the three steps fails, tell us as soon as possible.** 

---

## Notebooks

Every link opens the notebook directly in Colab.

### Day 1 - setup, data processing and first model

| | Notebook | |
|---|---|---|
| 0 | [0_Test](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/0_Test.ipynb) | Test notebook, checking if everything works, with some Python basics. |
| 1a | [1a_EDA_data_processing](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/1a_EDA_data_processing.ipynb) | Exploratory analysis and data processing on the Ames Housing dataset: missing values, outliers, encoding, scaling, train/test split and feature selection. |
| 1b | [1b_First_model](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/1b_First_model.ipynb) | A baseline and a linear regression on the prepared data, with residual analysis. Produces the score every later model is compared against. |
| 1c | [1c_Hands_on_two_houses](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/1c_Hands_on_two_houses.ipynb) | **HANDS-ON.** Two houses break the relationship between area and price. Find out why, and decide whether to remove them. |

Optional, not covered during the course:

| | Notebook | |
|---|---|---|
| 1x | [1x_Going_further_feature_selection](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/1x_Going_further_feature_selection.ipynb) | Wrapper and embedded feature selection methods, continuing Part 5 of 1a. |
| 1y | [1y_Going_further_classification](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/1y_Going_further_classification.ipynb) | The same processing steps applied to a classification problem, on the Iris dataset used again on day 2. |

Notebooks 1b and 1x read the train/test split saved by 1a. The Ames Housing
dataset is used throughout the day.

### Day 2 - supervised learning (regression and classification), unsupervised learning

|    | Notebook                                                                                                                                                            |                                                                                                                                           |
|----|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| 2a | [2a_Regression_Fundamentals](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/2a_Regression_Fundamentals.ipynb) | Simple linear regression on one housing feature, progressively adding more features, then Ridge and Lasso regularization on the full set. |
| 2b | [2b_KNN_Classification](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/2b_KNN_Classification.ipynb)           | K-Nearest Neighbors classification on the Iris dataset, exploring how the number of neighbours changes the decision boundary.             |
| 2c | [2c_Logistic_Regression](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/2c_Logistic_Regression.ipynb)         | Binary logistic regression boundaries, their linear limitation, and extension to three Iris classes with softmax.                         |
| 2d | [2d_Decision_Trees_and_SVM](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/2d_Decision_Trees_and_SVM.ipynb)   | Decision tree on Iris petals, then SVM margins and kernel comparison on small 2D datasets.                                                |
| 3  | [3_Unsupervised_learning](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/3_Unsupervised_learning.ipynb)     | Unsupervised learning with K-means clustering, hierarchical clustering, and PCA.                                                          |

### Day 3 - ensembles, hyperparameters tuning and interpretability

| | Notebook | |
|---|---|---|
| 3a | [3a_Cross-Validation](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/5_Cross-Validation.ipynb) | Cross-validation strategies and hyperparameter tuning. |
| 3b | [3b_Ensemble_Learning_House_Prices](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/6_Ensemble_Learning_House_Prices.ipynb) | Random forest, gradient boosting, and stacking on house prices. |
| 3c | [3c_Hyperparameters_Search](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/7_Hyperparameters_Search.ipynb) | Grid search, random search, and Bayesian optimization for hyperparameter tuning. |

### Day 4 - ANN, generative AI and agents

Notebooks 4b, 4c and 4d require the API key from step 2.

| | Notebook | |
|---|---|---|
| 4a | [4a_YOLO_object_detection](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4a_YOLO_object_detection.ipynb) | Object detection with a narrow model. |
| 4b | [4b_LLM_first_call](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4b_LLM_first_call.ipynb) | The raw HTTP call, system prompts, temperature, structured output, conversations, tokenization and cost. |
| 4c | [4c_Grounding_own_PDF](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4c_Grounding_own_PDF.ipynb) | Retrieval over a document of our own, and what happens when that document contains an instruction aimed at the model. |
| 4d | [4d_Workflow_vs_Agent](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4d_Workflow_vs_Agent.ipynb) | The same task solved as a fixed pipeline and as an agent, and the case where only one of them works. |

Notebooks 4b-4d import [`notebooks/lares_llm.py`](notebooks/lares_llm.py) — a
small shared module holding retries, token accounting and the model fallback
chain. Worth reading; it is about two hundred lines.

Optional, not covered during the course:

| | Notebook | |
|---|---|---|
| 4x | [4x_NN_House_prices](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4x_NN_House_prices.ipynb) | A simple MLP neural network for regression on the same housing data, implemented with Tensorflow and Keras. |
| 4y | [4y_NN_Iris](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4y_NN_Iris.ipynb) | A simple MLP neural network for classification on the Iris data, implemented with Tensorflow and Keras. |
| 4z | [4z_NN_Fashion_MNIST](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/4z_NN_Fashion_MNIST.ipynb) | A convolutional neural network for classification on the MNIST dataset. |

### Day 5 - private Kaggle competition

| | Notebook | |
|---|---|---|
| 5 | [5_Kaggle](https://colab.research.google.com/github/unizg-fer-lares/ai_bootcamp_foundations/blob/main/notebooks/5_Kaggle.ipynb) | Starter notebook for the competition: data loaded, a working baseline and a prepared submission cell. |

---

## While you work

**Your work is not saved automatically.** A Colab link opens a *copy* of the
notebook. If you close the tab without saving, your edits are gone.

- **File → Save a copy in Drive** — keeps it in your Google Drive
- **File → Download → Download .ipynb** — keeps it locally and uses no Drive
  space, useful if your Drive is full

**Everything can be re-run from the top.** If the connection drops or the
session is recycled, run the first cell again. Nothing depends on state you
cannot rebuild, so **Runtime → Restart and run all** is always safe.

**The first cell is called SETUP and always comes first.** It clones this
repository into the session and moves into `notebooks/`, which is what makes
every relative path work. Safe to run more than once, and it works unchanged
if you run the notebooks locally.

**Working locally instead:** **Code → Download ZIP**, then `jupyter lab` from
inside `notebooks/`. The SETUP cell detects that it is not in Colab and does
nothing. You will need to install the packages the notebooks import, and set
`GOOGLE_API_KEY` as an environment variable rather than as a Colab secret.

---

## If something goes wrong

### Accounts and access

| Symptom | Likely cause |
|---|---|
| Colab asks for unusual permissions, or will not open | corporate account with restrictions — use a personal one |
| "Google AI Studio is not available", or no **Create API key** button | same cause, or the account's age has not been verified |

### Errors from the model

| Error | What it means |
|---|---|
| **HTTP 429** | a rate limit; the code retries on its own, so wait. The message says *which* limit was hit — if it mentions *per day*, your daily quota is gone and the notebook moves to the fallback model by itself |
| **HTTP 503** | the model is overloaded on Google's side, nothing to do with your key; the code waits and then switches models |
| **HTTP 400** with a model name | model names change often — run the *"which models does this key actually have"* cell in notebook 4b to list the exact names your key accepts |
| **HTTP 403** | the key is invalid, or AI Studio is blocked on that account |
| answer stops mid-sentence | the output token budget ran out; raise `max_tokens` — the notebooks flag this explicitly when it happens |

### Errors from Colab

| Symptom | Fix |
|---|---|
| "Restart runtime" after installing a package | restart, then **Runtime → Restart and run all**; the SETUP cell survives it |
| `FileNotFoundError` on a path starting with `../data/` | the SETUP cell has not been run in this session |
| `ModuleNotFoundError` | an installation cell was skipped; they are at the top of each notebook |
| everything disappeared | the session was recycled after inactivity — re-run from the first cell |

---

## Layout

```
notebooks/    notebooks, plus lares_llm.py
data/         datasets, images and documents — fetched automatically
```

The material stays available after the course.
