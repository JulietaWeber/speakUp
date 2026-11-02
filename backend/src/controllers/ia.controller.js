
const supabase = require("../config/Supabase");

// =====================================
// CONFIGURACION
// =====================================

const obtenerUrlIA = () =>
  (process.env.IA_API_URL || "https://speakup-ia.onrender.com")
    .replace(/\/+$/, "");

const responderOk = (res, data) =>
  res.json({ data, error: null });

const responderError = (res, status, mensaje, detalle) => {
  const respuesta = { data: null, error: mensaje };
  if (detalle !== undefined) respuesta.detalle = detalle;
  return res.status(status).json(respuesta);
};

const leerRespuestaIA = async (respuesta) => {
  const texto = await respuesta.text();
  try {
    return JSON.parse(texto);
  } catch {
    return texto;
  }
};

const normalizarPalabras = (entrada) => {
  if (typeof entrada === "string") {
    return entrada.trim().split(/\s+/).filter(Boolean);
  }

  if (!Array.isArray(entrada)) return [];

  return entrada
    .filter((v) => typeof v === "string")
    .flatMap((v) => v.trim().split(/\s+/))
    .filter(Boolean);
};

const obtenerUltimasTresPalabras = (palabras) =>
  normalizarPalabras(palabras).slice(-3);

const normalizarBusqueda = (valor) =>
  String(valor || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");

const consultarIA = async (endpoint, payload) => {
  const respuesta = await fetch(
    `${obtenerUrlIA()}${endpoint}`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(60000)
    }
  );

  return {
    ok: respuesta.ok,
    status: respuesta.status,
    data: await leerRespuestaIA(respuesta)
  };
};

// =====================================
// HISTORIAL
// =====================================

const guardarHistorialIA = async (
  id_usuario,
  texto_actual,
  sugerencia,
  origen,
  accion,
  detalle
) => {
  const resultados = await Promise.allSettled([
    supabase.from("sugerencias_ia").insert([{
      id_usuario,
      texto_actual,
      sugerencia,
      origen
    }]),
    supabase.from("historial_uso").insert([{
      id_usuario,
      accion,
      detalle
    }])
  ]);

  for (const r of resultados) {
    if (r.status === "rejected") {
      console.error("Error historial IA:", r.reason);
    } else if (r.value.error) {
      console.error("Error historial IA:", r.value.error.message);
    }
  }
};

// =====================================
// BUSQUEDA DE PICTOGRAMAS
// =====================================

// Consulta nuestro catalogo general.
// No devuelve pictogramas personalizados de otros usuarios.
const buscarPictogramasLocales = async (palabra) => {
  const { data, error } = await supabase
    .from("pictogramas")
    .select("id_pictogramas, nombre, imagen_url")
    .eq("es_personalizado", false)
    .not("imagen_url", "is", null)
    .ilike("nombre", palabra.trim())
    .limit(20);

  if (error) {
    console.error("Error pictogramas Supabase:", error.message);
    return [];
  }

  return (data || [])
    .filter(
      (p) =>
        normalizarBusqueda(p.nombre) ===
        normalizarBusqueda(palabra)
    )
    .map((p) => ({
      id: `local-${p.id_pictogramas}`,
      id_pictograma: p.id_pictogramas,
      palabra: p.nombre,
      imagen_url: p.imagen_url,
      origen_imagen: "supabase"
    }));
};

// Los pictogramas ARASAAC se consultan sin modificar
// nuestro catalogo de Supabase.
const buscarPictogramasArasaac = async (
  palabra,
  limite = 8
) => {
  try {
    const termino = String(palabra || "").trim();
    if (!termino) return [];

    const url =
      "https://api.arasaac.org/v1/pictograms/es/bestsearch/" +
      encodeURIComponent(termino);

    const respuesta = await fetch(url, {
      headers: { Accept: "application/json" },
      signal: AbortSignal.timeout(5000)
    });

    if (!respuesta.ok) return [];

    const resultados = await respuesta.json();
    if (!Array.isArray(resultados)) return [];

    const vistos = new Set();
    const pictogramas = [];

    for (const item of resultados) {
      const id = Number(item._id);

      if (!Number.isSafeInteger(id) || id <= 0) continue;
      if (vistos.has(id)) continue;

      vistos.add(id);

      const palabrasClave = Array.isArray(item.keywords)
        ? item.keywords
            .map((k) => k.keyword || k.word)
            .filter((k) => typeof k === "string")
        : [];

      const coincidenciaExacta = palabrasClave.some(
        (k) =>
          normalizarBusqueda(k) ===
          normalizarBusqueda(termino)
      );

      pictogramas.push({
        id: `arasaac-${id}`,
        id_arasaac: id,
        palabra: termino,
        imagen_url:
          `https://static.arasaac.org/pictograms/${id}/${id}_300.png`,
        origen_imagen: "arasaac",
        coincidencia_exacta: coincidenciaExacta,
        palabras_clave: palabrasClave.slice(0, 8)
      });

      if (pictogramas.length >= limite) break;
    }

    // Mostrar primero las coincidencias exactas.
    return pictogramas.sort(
      (a, b) =>
        Number(b.coincidencia_exacta) -
        Number(a.coincidencia_exacta)
    );

  } catch (error) {
    console.error("Error consultando ARASAAC:", error.message);
    return [];
  }
};

// Busca en ambas fuentes.
// El buscador manual devuelve varias alternativas.
const obtenerOpcionesPictogramas = async (
  palabra,
  limite = 8
) => {
  const [locales, externos] = await Promise.all([
    buscarPictogramasLocales(palabra),
    buscarPictogramasArasaac(palabra, limite)
  ]);

  return {
    locales,
    externos,
    opciones: [...locales, ...externos].slice(0, limite)
  };
};

// Para las sugerencias automaticas, preferimos
// imagen local y luego una coincidencia exacta de ARASAAC.
const agregarImagenesPredicciones = async (predicciones) => {
  if (!Array.isArray(predicciones)) {
    return predicciones;
  }

  return Promise.all(
    predicciones.map(async (prediccion) => {
      if (
        !prediccion ||
        typeof prediccion.palabra !== "string"
      ) {
        return prediccion;
      }

      try {
        const busqueda = await obtenerOpcionesPictogramas(
          prediccion.palabra,
          5
        );

        const local = busqueda.locales[0];

        const externoExacto = busqueda.externos.find(
          (p) => p.coincidencia_exacta
        );

        const elegido = local || externoExacto || null;

        return {
          ...prediccion,
          imagen_url: elegido?.imagen_url || null,
          origen_imagen:
            elegido?.origen_imagen || "sin_imagen",
          id_arasaac: elegido?.id_arasaac || null
        };

      } catch (error) {
        console.error("Error imagen prediccion:", error);

        return {
          ...prediccion,
          imagen_url: null,
          origen_imagen: "sin_imagen",
          id_arasaac: null
        };
      }
    })
  );
};

// =====================================
// GET /ia/buscar-pictogramas?palabra=...
// =====================================

const buscarPictogramasIA = async (req, res) => {
  try {
    const palabra = String(
      req.query.palabra || ""
    ).trim();

    if (!palabra || palabra.length > 80) {
      return responderError(
        res,
        400,
        "Enviá una palabra de hasta 80 caracteres"
      );
    }

    const busqueda = await obtenerOpcionesPictogramas(
      palabra,
      10
    );

    return responderOk(res, {
      palabra,
      total: busqueda.opciones.length,
      pictogramas: busqueda.opciones
    });

  } catch (error) {
    console.error("Error buscador de pictogramas:", error);

    return responderError(
      res,
      502,
      "No se pudo completar la busqueda de pictogramas"
    );
  }
};

// =====================================
// GET /ia/ping
// =====================================

const pingIA = async (req, res) => {
  try {
    const respuesta = await fetch(
      `${obtenerUrlIA()}/ping`,
      { signal: AbortSignal.timeout(60000) }
    );

    const data = await leerRespuestaIA(respuesta);

    if (!respuesta.ok) {
      return responderError(
        res,
        502,
        "La API de IA respondio con error",
        data
      );
    }

    return responderOk(res, data);

  } catch (error) {
    console.error("Error ping IA:", error);

    return responderError(
      res,
      502,
      "No se pudo conectar con la API de IA"
    );
  }
};

// =====================================
// POST /ia/predecir
// =====================================

const predecirSiguientePalabra = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras, palabra } = req.body || {};

    const recibidas =
      palabras !== undefined
        ? normalizarPalabras(palabras)
        : normalizarPalabras(palabra);

    const ultimasTres =
      obtenerUltimasTresPalabras(recibidas);

    if (!ultimasTres.length) {
      return responderError(
        res, 400, "Tenes que enviar al menos una palabra"
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
        res, 502, "Error al consultar prediccion de IA",
        resultado.data
      );
    }

    const prediccionesConImagenes =
      await agregarImagenesPredicciones(resultado.data);

    await guardarHistorialIA(
      id_usuario,
      recibidas.join(" "),
      JSON.stringify(resultado.data),
      "ia_predecir",
      "ia_predecir",
      `Prediccion IA para: ${ultimasTres.join(" ")}`
    );

    return responderOk(res, {
      entrada: payloadIA,
      predicciones: prediccionesConImagenes
    });

  } catch (error) {
    console.error("Error predecir IA:", error);

    return responderError(
      res, 502, "No se pudo completar la prediccion de IA"
    );
  }
};

// =====================================
// POST /ia/corregir
// =====================================

const corregirFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res, 400, "Tenes que enviar palabras como array"
      );
    }

    const normalizadas = normalizarPalabras(palabras);

    if (!normalizadas.length) {
      return responderError(
        res, 400, "Tenes que enviar palabras como array"
      );
    }

    const payloadIA = { palabras: normalizadas };

    const resultado = await consultarIA(
      "/corregir",
      payloadIA
    );

    if (!resultado.ok) {
      return responderError(
        res, 502, "Error al corregir frase con IA",
        resultado.data
      );
    }

    const fraseCorregida =
      typeof resultado.data?.frase === "string"
        ? resultado.data.frase
        : normalizadas.join(" ");

    await guardarHistorialIA(
      id_usuario,
      normalizadas.join(" "),
      fraseCorregida,
      "ia_corregir",
      "ia_corregir",
      `Correccion IA: ${fraseCorregida}`
    );

    return responderOk(res, {
      entrada: payloadIA,
      frase_corregida: fraseCorregida,
      respuesta_original: resultado.data
    });

  } catch (error) {
    console.error("Error corregir IA:", error);

    return responderError(
      res, 502, "No se pudo completar la correccion de IA"
    );
  }
};

// =====================================
// POST /ia/procesar-frase
// =====================================

const procesarFraseConIA = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras, categoria } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res, 400, "Tenes que enviar palabras como array"
      );
    }

    const normalizadas = normalizarPalabras(palabras);

    if (!normalizadas.length) {
      return responderError(
        res, 400, "No hay palabras validas para procesar"
      );
    }

    const categoriaFinal =
      categoria ? String(categoria) : "general";

    // 1. Corregir
    const resultadoCorregir = await consultarIA(
      "/corregir",
      { palabras: normalizadas }
    );

    if (!resultadoCorregir.ok) {
      return responderError(
        res, 502, "Error al corregir frase con IA",
        resultadoCorregir.data
      );
    }

    const fraseCorregida =
      typeof resultadoCorregir.data?.frase === "string"
        ? resultadoCorregir.data.frase
        : normalizadas.join(" ");

    // 2. Predecir
    const ultimasTres =
      obtenerUltimasTresPalabras(normalizadas);

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
        res, 502,
        "Error al predecir siguiente palabra con IA",
        resultadoPredecir.data
      );
    }

    // 3. Buscar imagenes
    const prediccionesConImagenes =
      await agregarImagenesPredicciones(
        resultadoPredecir.data
      );

    // 4. Guardar historial
    await guardarHistorialIA(
      id_usuario,
      normalizadas.join(" "),
      JSON.stringify({
        frase_corregida: fraseCorregida,
        predicciones: resultadoPredecir.data
      }),
      "ia_procesar_frase",
      "ia_procesar_frase",
      `Frase procesada con IA: ${fraseCorregida}`
    );

    // 5. Responder al frontend
    return responderOk(res, {
      frase_original: normalizadas,
      categoria: categoriaFinal,
      frase_corregida: fraseCorregida,
      palabra_base_prediccion:
        ultimasTres[ultimasTres.length - 1],
      predicciones: prediccionesConImagenes
    });

  } catch (error) {
    console.error("Error procesar frase IA:", error);

    return responderError(
      res, 502, "No se pudo procesar la frase con IA"
    );
  }
};

// =====================================
// EXPORTS
// =====================================

module.exports = {
  pingIA,
  predecirSiguientePalabra,
  corregirFrase,
  procesarFraseConIA,
  buscarPictogramasIA
};
