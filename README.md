# Waste Sorting Image Classifier

This image classifier tells you which bin a piece of household waste belongs in: PMD (plastic, metal and drink cartons), paper and cardboard, organic, or general waste. It is the AI behind **Smart Bin**, a recycling assistant app prototype.

It was an individual university project at Breda University of Applied Sciences (Applied Data Science & AI, Year 1), from February to April 2025. The client was BUas Innovation Square.

## The problem

Many people want to recycle but don't know which bin an item belongs in, and contaminated recycling loads often end up in landfill. Existing recycling apps make users look items up by name. The idea was to let users take a photo instead and get the right bin straight away.

## How it works

1. **Dataset.** 400 photorealistic images, 100 per class, generated with the FLUX.1 Schnell text-to-image model through ComfyUI.
   - Each class has five prompts describing realistic scenes, for example a mix of plastic bottles, cans and juice cartons on a wooden table.
   - Every image was checked by hand; unrealistic images and duplicates were replaced.
   - Split: 80% training, 10% validation, 10% test (324 / 36 / 40 images).
2. **Baselines.**
   - A random guess.
   - A multilayer perceptron on flattened pixels, tuned over three learning rates.
   - Human performance: three people classified 40 images in a quiz.
3. **Four CNN iterations,** each evaluated on the same test set with a confusion matrix and per-class precision, recall and F1:
   1. A small custom CNN: three convolutional blocks (128, 64 and 32 filters), batch normalisation, dropout and global average pooling, on 128 px images.
   2. The same network trained with data augmentation: rotation, shifts, zoom, shear and flips.
   3. Transfer learning: a frozen MobileNet (ImageNet weights) on 224 px images, with a small dense classifier on top.
   4. MobileNet with the augmentation layers built into the model.
4. **Error analysis.** The iteration 2 model's mistakes were grouped by cause, such as similar shapes and textures or a distracting scene, and improvements were proposed.
5. **Responsible AI.**
   - A bias analysis of the imSitu dataset found gender imbalance in roles such as "cooking" and "leading", and an individual fairness method was proposed.
   - Grad-CAM (Xplique) shows which parts of an image drive the classifier's predictions.
6. **Product and user research.**
   - Market research, a stakeholder analysis and a decision framework for the Smart Bin app.
   - A Figma prototype evaluated with a think-aloud study and an A/B test.
   - See [docs/product-research.md](docs/product-research.md).

## Results

| Model | Test accuracy |
|---|---|
| Random guess | 25.0% |
| Multilayer perceptron (learning rate 0.001) | 67.5% |
| Human level (3 people) | 78.3% |
| Iteration 1: custom CNN | 72.5% (weighted F1 0.71) |
| Iteration 2: custom CNN + data augmentation | 85.0% (weighted F1 0.85) |
| Iteration 3: MobileNet transfer learning | 97.5% |
| Iteration 4: MobileNet + built-in augmentation | **100%** (40 of 40) |

Transfer learning gave the biggest jump: from 85% with the best custom CNN to 97.5–100%, well above the human baseline. The test set is small (40 images) and, like the training data, AI-generated. The model was not tested on real photos, so these figures likely overstate real-world accuracy.

In the A/B test of the app prototype (10 participants per version), adding a feedback button made no significant difference to perceived usefulness (t(18) = 1.23, p = 0.23).

## My role

This was an individual project; everything here is my work:

- the problem framing and market research
- the dataset prompts and generation
- the baselines, all four model iterations and the error analysis
- the bias analysis and explainability
- the Figma prototype and both user studies

The course provided the notebook templates and the ComfyUI example that the generation script is based on.

## Tech stack

Python, TensorFlow/Keras, MobileNet, scikit-learn, NumPy, pandas, SciPy, Matplotlib, Xplique (Grad-CAM), ComfyUI with FLUX.1 Schnell, Figma.

## Repository layout

```
notebooks/
  01_waste_classifier.ipynb   # dataset loading, baselines, four CNN iterations, error analysis
  02_responsible_ai.ipynb     # imSitu bias analysis, fairness method, Grad-CAM
  03_ab_test_analysis.ipynb   # t-test on the prototype A/B survey
src/
  generate_dataset.py         # image generation through a ComfyUI server
docs/
  product-research.md         # market research, stakeholders, prototype, user studies
  images/daps-diagram.svg     # decision framework diagram
```

## Data and models

The generated images, trained models and survey responses are not included. To run the notebooks, place them like this (these folders are ignored by git):

```
data/
  dataset/<class name>/*.png   # PMD, Paper & Cardboard, Organic Waste, General Waste
  ab_test_version_a.xlsx       # survey responses (notebook 03)
  ab_test_version_b.xlsx
models/
  model_it2.h5                 # written by notebook 01, used by notebook 02
```

## How to run

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

1. **Generate the dataset (optional).** This needs access to a ComfyUI server running FLUX.1 Schnell, and its workflow exported in API format.
   1. Copy `.env.example` to `.env`.
   2. Fill in the server address and login.
   3. Run:

      ```bash
      python src/generate_dataset.py --images-per-class 100 --out data/dataset
      ```

2. **Run the notebooks** in `notebooks/` in order.
