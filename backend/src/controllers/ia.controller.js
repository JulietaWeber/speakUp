const supabase = require("../config/Supabase");

const obtenerUrlIA = () => {
  return process.env.IA_API_URL || "https://speakup-ia.onrender.com";
};

const leerRespuestaIA = async (respuesta) => {
  const texto = await respuesta.text();

  try {
    return JSON.parse(texto);
  } catch (error) {
    return texto;
  }
};

// GET /ia/ping
const pingIA = async (req, res) => {
  try {
    const IA_API_URL = obtenerUrlIA();

    const respuesta = await fetch(`${IA_API_URL}/ping`);
    const dataIA = await leerRespuestaIA(respuesta);

    if (!respuesta.ok) {
      return res.status(502).json({
        data: null,
        error: "La API de IA respondió con error",
        detalle: dataIA
      });
    }

    return res.json({
      data: dataIA,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /ia/predecir
const predecirSiguientePalabra = async (req, res) => {
  try {
    const IA_API_URL = obtenerUrlIA();
    const id_usuario = req.usuario.id_usuario;

    const { categoria, palabra } = req.body;

    if (!categoria || !palabra) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: categoria y palabra"
      });
    }

    const payloadIA = {
      user_id: String(id_usuario),
      categoria: String(categoria),
      palabra: String(palabra)
    };

    const respuesta = await fetch(`${IA_API_URL}/predecir`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payloadIA)
    });

    const dataIA = await leerRespuestaIA(respuesta);

    if (!respuesta.ok) {
      return res.status(502).json({
        data: null,
        error: "Error al consultar predicción de IA",
        detalle: dataIA
      });
    }

    await supabase.from("sugerencias_ia").insert([
      {
        id_usuario,
        texto_actual: palabra,
        sugerencia: JSON.stringify(dataIA),
        origen: "ia_predecir"
      }
    ]);

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "ia_predecir",
        detalle: `Predicción IA para palabra: ${palabra}`
      }
    ]);

    return res.json({
      data: {
        entrada: payloadIA,
        predicciones: dataIA
      },
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /ia/corregir
const corregirFrase = async (req, res) => {
  try {
    const IA_API_URL = obtenerUrlIA();
    const id_usuario = req.usuario.id_usuario;

    const { palabras } = req.body;

    if (!palabras || !Array.isArray(palabras) || palabras.length === 0) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar palabras como array"
      });
    }

    const payloadIA = {
      palabras: palabras.map((palabra) => String(palabra))
    };

    const respuesta = await fetch(`${IA_API_URL}/corregir`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payloadIA)
    });

    const dataIA = await leerRespuestaIA(respuesta);

    if (!respuesta.ok) {
      return res.status(502).json({
        data: null,
        error: "Error al corregir frase con IA",
        detalle: dataIA
      });
    }

    const fraseCorregida =
      dataIA && dataIA.frase
        ? dataIA.frase
        : palabras.join(" ");

    await supabase.from("sugerencias_ia").insert([
      {
        id_usuario,
        texto_actual: palabras.join(" "),
        sugerencia: fraseCorregida,
        origen: "ia_corregir"
      }
    ]);

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "ia_corregir",
        detalle: `Corrección IA: ${fraseCorregida}`
      }
    ]);

    return res.json({
      data: {
        entrada: payloadIA,
        frase_corregida: fraseCorregida,
        respuesta_original: dataIA
      },
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /ia/procesar-frase
const procesarFraseConIA = async (req, res) => {
  try {
    const IA_API_URL = obtenerUrlIA();
    const id_usuario = req.usuario.id_usuario;

    const { palabras, categoria } = req.body;

    if (!palabras || !Array.isArray(palabras) || palabras.length === 0) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar palabras como array"
      });
    }

    const palabrasNormalizadas = palabras
      .map((palabra) => String(palabra).trim())
      .filter(Boolean);

    if (palabrasNormalizadas.length === 0) {
      return res.status(400).json({
        data: null,
        error: "No hay palabras válidas para procesar"
      });
    }

    const categoriaFinal = categoria ? String(categoria) : "general";

    // 1. Corregir frase con IA
    const respuestaCorregir = await fetch(`${IA_API_URL}/corregir`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        palabras: palabrasNormalizadas
      })
    });

    const dataCorregir = await leerRespuestaIA(respuestaCorregir);

    if (!respuestaCorregir.ok) {
      return res.status(502).json({
        data: null,
        error: "Error al corregir frase con IA",
        detalle: dataCorregir
      });
    }

    const fraseCorregida =
      dataCorregir && dataCorregir.frase
        ? dataCorregir.frase
        : palabrasNormalizadas.join(" ");

    // 2. Tomar última palabra para predecir la siguiente
    const ultimaPalabra = palabrasNormalizadas[palabrasNormalizadas.length - 1];

    const respuestaPredecir = await fetch(`${IA_API_URL}/predecir`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        user_id: String(id_usuario),
        categoria: categoriaFinal,
        palabra: ultimaPalabra
      })
    });

    const dataPredecir = await leerRespuestaIA(respuestaPredecir);

    if (!respuestaPredecir.ok) {
      return res.status(502).json({
        data: null,
        error: "Error al predecir siguiente palabra con IA",
        detalle: dataPredecir
      });
    }

    // 3. Guardar sugerencia IA
    await supabase.from("sugerencias_ia").insert([
      {
        id_usuario,
        texto_actual: palabrasNormalizadas.join(" "),
        sugerencia: JSON.stringify({
          frase_corregida: fraseCorregida,
          predicciones: dataPredecir
        }),
        origen: "ia_procesar_frase"
      }
    ]);

    // 4. Guardar historial
    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "ia_procesar_frase",
        detalle: `Frase procesada con IA: ${fraseCorregida}`
      }
    ]);

    return res.json({
      data: {
        frase_original: palabrasNormalizadas,
        categoria: categoriaFinal,
        frase_corregida: fraseCorregida,
        palabra_base_prediccion: ultimaPalabra,
        predicciones: dataPredecir
      },
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

module.exports = {
  pingIA,
  predecirSiguientePalabra,
  corregirFrase,
  procesarFraseConIA
};