
const supabase = require("../config/Supabase");

// =====================
// CONFIGURACIÓN
// =====================

const obtenerUrlIA = () => {
  return (
    process.env.IA_API_URL ||
    "https://speakup-ia.onrender.com"
  ).replace(/\/+$/, "");
};

const leerRespuestaIA = async (respuesta) => {
  const texto = await respuesta.text();

  try {
    return JSON.parse(texto);
  } catch {
    return texto;
  }
};

const responderOk = (res, data) => {
  return res.json({
    data,
    error: null
  });
};

const responderError = (res, status, mensaje, detalle) => {
  const respuesta = {
    data: null,
    error: mensaje
  };

  if (detalle !== undefined) {
    respuesta.detalle = detalle;
  }

  return res.status(status).json(respuesta);
};

// =====================
// HELPERS DE IA
// =====================

// Convierte la entrada en una lista de palabras.
// Acepta el array nuevo o una palabra del frontend anterior.
const normalizarPalabras = (entrada) => {
  if (typeof entrada === "string") {
    return entrada.trim().split(/\s+/).filter(Boolean);
  }

  if (!Array.isArray(entrada)) {
    return [];
  }

  return entrada
    .filter((valor) => typeof valor === "string")
    .flatMap((valor) => valor.trim().split(/\s+/))
    .filter(Boolean);
};

// La IA ahora recibe solamente las últimas 3 palabras.
const obtenerUltimasTresPalabras = (palabras) => {
  return normalizarPalabras(palabras).slice(-3);
};

// Unifica la llamada HTTP a la IA.
const consultarIA = async (endpoint, payload) => {
  const respuesta = await fetch(
    `${obtenerUrlIA()}${endpoint}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(60000)
    }
  );

  const data = await leerRespuestaIA(respuesta);

  return {
    ok: respuesta.ok,
    status: respuesta.status,
    data
  };
};

// Guardar historial sin interrumpir una predicción exitosa.
const guardarHistorialIA = async (
  id_usuario,
  texto_actual,
  sugerencia,
  origen,
  accion,
  detalle
) => {
  const resultados = await Promise.allSettled([
    supabase.from("sugerencias_ia").insert([
      {
        id_usuario,
        texto_actual,
        sugerencia,
        origen
      }
    ]),
    supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion,
        detalle
      }
    ])
  ]);

  for (const resultado of resultados) {
    if (resultado.status === "rejected") {
      console.error(
        "Error guardando historial IA:",
        resultado.reason
      );
    } else if (resultado.value.error) {
      console.error(
        "Error guardando historial IA:",
        resultado.value.error.message
      );
    }
  }
};

// =====================
// GET /ia/ping
// =====================

const pingIA = async (req, res) => {
  try {
    const respuesta = await fetch(
      `${obtenerUrlIA()}/ping`,
      {
        signal: AbortSignal.timeout(60000)
      }
    );

    const dataIA = await leerRespuestaIA(respuesta);

    if (!respuesta.ok) {
      return responderError(
        res,
        502,
        "La API de IA respondió con error",
        dataIA
      );
    }

    return responderOk(res, dataIA);
  } catch (error) {
    console.error("Error ping IA:", error);
    return responderError(
      res,
      502,
      "No se pudo conectar con la API de IA"
    );
  }
};

// =====================
// POST /ia/predecir
// =====================

const predecirSiguientePalabra = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    // Nuevo formato: { palabras: [...] }
    // Formato anterior: { categoria, palabra }
    // La categoría ya no se envía a la IA.
    const { palabras, palabra } = req.body || {};

    const palabrasRecibidas =
      palabras !== undefined
        ? normalizarPalabras(palabras)
        : normalizarPalabras(palabra);

    const ultimasTres =
      obtenerUltimasTresPalabras(palabrasRecibidas);

    if (ultimasTres.length === 0) {
      return responderError(
        res,
        400,
        "Tenés que enviar al menos una palabra"
      );
    }

    const payloadIA = {
      user_id: String(id_usuario),
      palabras: ultimasTres
    };

    const resultado = await consultarIA(
      "/predecir",
      payloadIA
    );

    if (!resultado.ok) {
      return responderError(
        res,
        502,
        "Error al consultar predicción de IA",
        resultado.data
      );
    }

    await guardarHistorialIA(
      id_usuario,
      palabrasRecibidas.join(" "),
      JSON.stringify(resultado.data),
      "ia_predecir",
      "ia_predecir",
      `Predicción IA para: ${ultimasTres.join(" ")}`
    );

    return responderOk(res, {
      entrada: payloadIA,
      predicciones: resultado.data
    });

  } catch (error) {
    console.error("Error predecir IA:", error);

    return responderError(
      res,
      502,
      "No se pudo completar la predicción de IA"
    );
  }
};

// =====================
// POST /ia/corregir
// =====================

const corregirFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res,
        400,
        "Tenés que enviar palabras como array"
      );
    }

    const palabrasNormalizadas =
      normalizarPalabras(palabras);

    if (palabrasNormalizadas.length === 0) {
      return responderError(
        res,
        400,
        "Tenés que enviar palabras como array"
      );
    }

    const payloadIA = {
      palabras: palabrasNormalizadas
    };

    const resultado = await consultarIA(
      "/corregir",
      payloadIA
    );

    if (!resultado.ok) {
      return responderError(
        res,
        502,
        "Error al corregir frase con IA",
        resultado.data
      );
    }

    const fraseCorregida =
      resultado.data &&
      typeof resultado.data.frase === "string"
        ? resultado.data.frase
        : palabrasNormalizadas.join(" ");

    await guardarHistorialIA(
      id_usuario,
      palabrasNormalizadas.join(" "),
      fraseCorregida,
      "ia_corregir",
      "ia_corregir",
      `Corrección IA: ${fraseCorregida}`
    );

    return responderOk(res, {
      entrada: payloadIA,
      frase_corregida: fraseCorregida,
      respuesta_original: resultado.data
    });

  } catch (error) {
    console.error("Error corregir IA:", error);

    return responderError(
      res,
      502,
      "No se pudo completar la corrección de IA"
    );
  }
};

// =====================
// POST /ia/procesar-frase
// =====================

const procesarFraseConIA = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras, categoria } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res,
        400,
        "Tenés que enviar palabras como array"
      );
    }

    const palabrasNormalizadas =
      normalizarPalabras(palabras);

    if (palabrasNormalizadas.length === 0) {
      return responderError(
        res,
        400,
        "No hay palabras válidas para procesar"
      );
    }

    // Conservamos categoria en la respuesta al frontend
    // para no romper el contrato existente.
    const categoriaFinal =
      categoria ? String(categoria) : "general";

    // 1. CORREGIR LA FRASE COMPLETA
    const resultadoCorregir = await consultarIA(
      "/corregir",
      {
        palabras: palabrasNormalizadas
      }
    );

    if (!resultadoCorregir.ok) {
      return responderError(
        res,
        502,
        "Error al corregir frase con IA",
        resultadoCorregir.data
      );
    }

    const fraseCorregida =
      resultadoCorregir.data &&
      typeof resultadoCorregir.data.frase === "string"
        ? resultadoCorregir.data.frase
        : palabrasNormalizadas.join(" ");

    // 2. PREDECIR CON LAS ÚLTIMAS 3 PALABRAS
    const ultimasTres =
      obtenerUltimasTresPalabras(palabrasNormalizadas);

    const payloadPrediccion = {
      user_id: String(id_usuario),
      palabras: ultimasTres
    };

    const resultadoPredecir = await consultarIA(
      "/predecir",
      payloadPrediccion
    );

    if (!resultadoPredecir.ok) {
      return responderError(
        res,
        502,
        "Error al predecir siguiente palabra con IA",
        resultadoPredecir.data
      );
    }

    const ultimaPalabra =
      ultimasTres[ultimasTres.length - 1];

    // 3. GUARDAR SUGERENCIA E HISTORIAL
    await guardarHistorialIA(
      id_usuario,
      palabrasNormalizadas.join(" "),
      JSON.stringify({
        frase_corregida: fraseCorregida,
        predicciones: resultadoPredecir.data
      }),
      "ia_procesar_frase",
      "ia_procesar_frase",
      `Frase procesada con IA: ${fraseCorregida}`
    );

    // 4. RESPUESTA AL FRONTEND
    return responderOk(res, {
      frase_original: palabrasNormalizadas,
      categoria: categoriaFinal,
      frase_corregida: fraseCorregida,
      palabra_base_prediccion: ultimaPalabra,
      predicciones: resultadoPredecir.data
    });

  } catch (error) {
    console.error("Error procesar frase IA:", error);

    return responderError(
      res,
      502,
      "No se pudo procesar la frase con IA"
    );
  }
};

// =====================
// EXPORTS
// =====================

module.exports = {
  pingIA,
  predecirSiguientePalabra,
  corregirFrase,
  procesarFraseConIA
};
