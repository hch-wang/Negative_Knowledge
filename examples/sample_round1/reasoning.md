# Round 1 reasoning

Plan: fit a RandomForestRegressor on the training data, then use SHAP's
TreeExplainer to get exact per-feature attributions and save them to
`pred_results/importances.csv`. SHAP gives principled tree attributions,
so it should be the most faithful importance measure here.
