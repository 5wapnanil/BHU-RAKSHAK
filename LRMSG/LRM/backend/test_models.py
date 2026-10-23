from app.model.model_loader import load_all_models


def main():
    print("Loading all frozen models...")

    models = load_all_models()

    print("\nXGBoost model: LOADED")
    print(type(models["xgboost"]))

    print("\nAHC model: LOADED")
    print(type(models["ahc"]))

    print("\nDecision model: LOADED")
    print(type(models["decision"]))

    print("\nALL THREE MODELS LOADED SUCCESSFULLY.")


if __name__ == "__main__":
    main()