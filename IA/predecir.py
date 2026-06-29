import joblib

# Cargar modelo
modelo = joblib.load("modelo_base.pkl")
encoder_categoria = joblib.load("encoder_categoria.pkl")
encoder_palabra = joblib.load("encoder_palabra.pkl")

# Datos de entrada (después vendrán del backend)
categoria = "Casa"
palabra = "quiero"

entrada = [[
    encoder_categoria.transform([categoria])[0],
    encoder_palabra.transform([palabra])[0]
]]

probabilidades = modelo.predict_proba(entrada)[0]
top3_indices = probabilidades.argsort()[-3:][::-1]

for indice in top3_indices:
    clase_real = modelo.classes_[indice]
    palabra = encoder_palabra.inverse_transform([clase_real])[0]
    print(palabra)