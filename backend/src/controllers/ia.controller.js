
const supabase = require("../config/Supabase");

// ======================================
// CONFIGURACION GENERAL
// ======================================

const obtenerUrlIA = () => {
  return (
    process.env.IA_API_URL ||
    "https://speakup-ia.onrender.com"
  ).replace(/\/+$/, "");
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

const leerRespuestaIA = async (respuesta) => {
  const texto = await respuesta.text();

  try {
    return JSON.parse(texto);
  } catch {
    return texto;
  }
};

// ======================================
// NORMALIZACION
// ======================================

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

const obtenerUltimasTresPalabras = (palabras) => {
  return normalizarPalabras(palabras).slice(-3);
};

const normalizarBusqueda = (valor) => {
  return String(valor || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
};

// ======================================
// VERBOS EN INFINITIVO
// ======================================

// Diccionario inicial del MVP.
// Agregar aqui nuevas conjugaciones cuando sea necesario.
// No se cambia lo que muestra el frontend.

const VERBOS_BASE = {
  // TENER
  tengo: "tener",
  tienes: "tener",
  tiene: "tener",
  tenemos: "tener",
  tienen: "tener",
  tenia: "tener",
  tenias: "tener",
  teniamos: "tener",
  tenian: "tener",
  tendre: "tener",
  tendra: "tener",

  // QUERER
  quiero: "querer",
  quieres: "querer",
  quiere: "querer",
  queremos: "querer",
  quieren: "querer",
  queria: "querer",
  querias: "querer",
  queriamos: "querer",
  querian: "querer",

  // NECESITAR
  necesito: "necesitar",
  necesitas: "necesitar",
  necesita: "necesitar",
  necesitamos: "necesitar",
  necesitan: "necesitar",
  necesitaba: "necesitar",
  necesitaban: "necesitar",

  // GUSTAR
  gusto: "gustar",
  gustas: "gustar",
  gusta: "gustar",
  gustamos: "gustar",
  gustan: "gustar",
  gustaba: "gustar",
  gustaban: "gustar",
  gustaria: "gustar",
  gustarian: "gustar",
  gustara: "gustar",
  gustaran: "gustar",
  gustaron: "gustar",
  gusto: "gustar",

  // IR
  voy: "ir",
  vas: "ir",
  va: "ir",
  vamos: "ir",
  van: "ir",
  iba: "ir",
  ibas: "ir",
  ibamos: "ir",
  iban: "ir",
  fui: "ir",
  fueron: "ir",
  ire: "ir",
  iremos: "ir",

  // ESTAR
  estoy: "estar",
  estas: "estar",
  esta: "estar",
  estamos: "estar",
  estan: "estar",
  estaba: "estar",
  estaban: "estar",
  estuve: "estar",

  // PODER
  puedo: "poder",
  puedes: "poder",
  puede: "poder",
  podemos: "poder",
  pueden: "poder",
  podia: "poder",
  podian: "poder",
  podre: "poder",

  // HACER
  hago: "hacer",
  haces: "hacer",
  hace: "hacer",
  hacemos: "hacer",
  hacen: "hacer",
  hacia: "hacer",
  hicieron: "hacer",
  hice: "hacer",

  // COMER
  como: "comer",
  comes: "comer",
  come: "comer",
  comemos: "comer",
  comen: "comer",
  comia: "comer",
  comieron: "comer",

  // BEBER
  bebo: "beber",
  bebes: "beber",
  bebe: "beber",
  bebemos: "beber",
  beben: "beber",
  bebia: "beber",

  // JUGAR
  juego: "jugar",
  juegas: "jugar",
  juega: "jugar",
  jugamos: "jugar",
  juegan: "jugar",
  jugaba: "jugar",
  jugaron: "jugar",

  // SENTIR
  siento: "sentir",
  sientes: "sentir",
  siente: "sentir",
  sentimos: "sentir",
  sienten: "sentir",
  sentia: "sentir",

  // HABLAR
  hablo: "hablar",
  hablas: "hablar",
  habla: "hablar",
  hablamos: "hablar",
  hablan: "hablar",

  // TRABAJAR
  trabajo: "trabajar",
  trabajas: "trabajar",
  trabaja: "trabajar",
  trabajamos: "trabajar",
  trabajan: "trabajar",

  // DORMIR
  duermo: "dormir",
  duermes: "dormir",
  duerme: "dormir",
  dormimos: "dormir",
  duermen: "dormir",

  // VER
  veo: "ver",
  ves: "ver",
  ve: "ver",
  vemos: "ver",
  ven: "ver",

  // SABER
  se: "saber",
  sabes: "saber",
  sabe: "saber",
  sabemos: "saber",
  saben: "saber"
};

// Algunas formas son ambiguas:
// "como" puede ser verbo o conector.
// "esta" puede ser verbo o demostrativo.
// "se" puede ser verbo o pronombre.
//
// No aplicamos infinitivo automaticamente en esos casos.

const FORMAS_AMBIGUAS = new Set([
  "como",
  "esta",
  "se",
  "ve",
  "ven",
  "gusto",
  "trabajo",
  "hablo"
]);

const obtenerPalabraBase = (palabra) => {
  const normalizada = normalizarBusqueda(palabra);

  if (FORMAS_AMBIGUAS.has(normalizada)) {
    return null;
  }

  return VERBOS_BASE[normalizada] || null;
};

// Evitar pictogramas externos equivocados
// en palabras cuya funcion es principalmente gramatical.

const PALABRAS_FUNCIONALES = new Set([
  "porque",
  "por que",
  "para",
  "de",
  "del",
  "a",
  "al",
  "que",
  "y",
  "o",
  "el",
  "la",
  "los",
  "las",
  "un",
  "una",
  "en",
  "con",
  "sin",
  "mi",
  "tu",
  "su"
]);

// ======================================
// CONEXION CON LA IA DE RENDER
// ======================================

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

  return {
    ok: respuesta.ok,
    status: respuesta.status,
    data: await leerRespuestaIA(respuesta)
  };
};

// ======================================
// HISTORIAL
// ======================================

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

// ======================================
// BUSCAR PICTOGRAMAS EN SUPABASE
// ======================================

const buscarPictogramasLocales = async (palabra) => {
  try {
    const { data, error } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre, imagen_url")
      .eq("es_personalizado", false)
      .ilike("nombre", palabra.trim())
      .not("imagen_url", "is", null)
      .limit(20);

    if (error) {
      console.error("Error Supabase:", error.message);
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
        origen_imagen: "supabase",
        coincidencia_exacta: true
      }));

  } catch (error) {
    console.error("Error busqueda local:", error);
    return [];
  }
};

// ======================================
// BUSCAR PICTOGRAMAS EN ARASAAC
// ======================================

const buscarPictogramasArasaac = async (
  palabra,
  limite = 8
) => {
  try {
    const termino = String(palabra || "").trim();

    if (!termino) {
      return [];
    }

    const url =
      "https://api.arasaac.org/v1/pictograms/es/bestsearch/" +
      encodeURIComponent(termino);

    const respuesta = await fetch(url, {
      headers: {
        Accept: "application/json"
      },
      signal: AbortSignal.timeout(5000)
    });

    if (!respuesta.ok) {
      return [];
    }

    const resultados = await respuesta.json();

    if (!Array.isArray(resultados)) {
      return [];
    }

    const vistos = new Set();
    const pictogramas = [];

    for (const item of resultados) {
      const id = Number(item._id);

      if (
        !Number.isSafeInteger(id) ||
        id <= 0 ||
        vistos.has(id)
      ) {
        continue;
      }

      vistos.add(id);

      const palabrasClave = Array.isArray(item.keywords)
        ? item.keywords
            .map((k) => k.keyword || k.word)
            .filter((k) => typeof k === "string")
        : [];

      const coincidenciaExacta = palabrasClave.some(
        (keyword) =>
          normalizarBusqueda(keyword) ===
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
    }

    return pictogramas
      .sort(
        (a, b) =>
          Number(b.coincidencia_exacta) -
          Number(a.coincidencia_exacta)
      )
      .slice(0, limite);

  } catch (error) {
    console.error("Error ARASAAC:", error.message);
    return [];
  }
};

// ======================================
// BUSQUEDA GENERAL
// ======================================

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

// ======================================
// ELEGIR UNA IMAGEN PARA UNA PALABRA
// ======================================

// Primero usamos la palabra original.
// Luego, si no encontramos imagen, su infinitivo.

const buscarImagenParaPalabra = async (palabra) => {
  const busquedaOriginal =
    await obtenerOpcionesPictogramas(palabra, 8);

  // Preferencia 1: pictograma propio.
  const local = busquedaOriginal.locales[0];

  if (local) {
    return {
      ...local,
      palabra_base: palabra
    };
  }

  // Preferencia 2: coincidencia exacta de ARASAAC.
  const funcional = PALABRAS_FUNCIONALES.has(
    normalizarBusqueda(palabra)
  );

  if (!funcional) {
    const externaExacta =
      busquedaOriginal.externos.find(
        (p) => p.coincidencia_exacta
      );

    if (externaExacta) {
      return {
        ...externaExacta,
        palabra_base: palabra
      };
    }
  }

  // Preferencia 3: buscar por infinitivo.
  const palabraBase = obtenerPalabraBase(palabra);

  if (palabraBase) {
    const busquedaBase =
      await obtenerOpcionesPictogramas(palabraBase, 8);

    const localBase = busquedaBase.locales[0];

    const externaBase = busquedaBase.externos.find(
      (p) => p.coincidencia_exacta
    );

    const elegida = localBase || externaBase;

    if (elegida) {
      return {
        ...elegida,
        palabra_base: palabraBase
      };
    }
  }

  return null;
};

// ======================================
// AGREGAR IMAGENES A PREDICCIONES
// ======================================

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
        const imagen = await buscarImagenParaPalabra(
          prediccion.palabra
        );

        return {
          ...prediccion,

          imagen_url: imagen?.imagen_url || null,

          origen_imagen:
            imagen?.origen_imagen || "sin_imagen",

          id_arasaac: imagen?.id_arasaac || null,

          palabra_base:
            imagen?.palabra_base ||
            obtenerPalabraBase(prediccion.palabra) ||
            prediccion.palabra
        };

      } catch (error) {
        console.error(
          "Error imagen prediccion:",
          error
        );

        return {
          ...prediccion,
          imagen_url: null,
          origen_imagen: "sin_imagen",
          id_arasaac: null,
          palabra_base: prediccion.palabra
        };
      }
    })
  );
};

// ======================================
// GET /ia/buscar-pictogramas
// ======================================

const buscarPictogramasIA = async (req, res) => {
  try {
    const palabra = String(
      req.query.palabra || ""
    ).trim();

    if (!palabra || palabra.length > 80) {
      return responderError(
        res,
        400,
        "Envia una palabra de hasta 80 caracteres"
      );
    }

    const busqueda =
      await obtenerOpcionesPictogramas(palabra, 10);

    // Si no hay imagenes exactas, ofrecer
    // busqueda por infinitivo.

    const palabraBase = obtenerPalabraBase(palabra);

    let opciones = busqueda.opciones;
    let terminoAlternativo = null;

    const hayCoincidencia = opciones.some(
      (p) =>
        p.origen_imagen === "supabase" ||
        p.coincidencia_exacta === true
    );

    if (!hayCoincidencia && palabraBase) {
      const alternativa =
        await obtenerOpcionesPictogramas(
          palabraBase,
          10
        );

      opciones = alternativa.opciones.map((p) => ({
        ...p,
        palabra,
        palabra_base: palabraBase
      }));

      terminoAlternativo = palabraBase;
    }

    return responderOk(res, {
      palabra,
      palabra_base: palabraBase,
      termino_alternativo: terminoAlternativo,
      total: opciones.length,
      pictogramas: opciones
    });

  } catch (error) {
    console.error("Error buscador pictogramas:", error);

    return responderError(
      res,
      502,
      "No se pudo completar la busqueda"
    );
  }
};

// ======================================
// GET /ia/ping
// ======================================

const pingIA = async (req, res) => {
  try {
    const respuesta = await fetch(
      `${obtenerUrlIA()}/ping`,
      {
        signal: AbortSignal.timeout(60000)
      }
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

// ======================================
// POST /ia/predecir
// ======================================

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
        res,
        400,
        "Tenes que enviar al menos una palabra"
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
        "Error al consultar prediccion de IA",
        resultado.data
      );
    }

    const prediccionesConImagenes =
      await agregarImagenesPredicciones(
        resultado.data
      );

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
      res,
      502,
      "No se pudo completar la prediccion"
    );
  }
};

// ======================================
// POST /ia/corregir
// ======================================

const corregirFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res,
        400,
        "Tenes que enviar palabras como array"
      );
    }

    const normalizadas = normalizarPalabras(palabras);

    if (!normalizadas.length) {
      return responderError(
        res,
        400,
        "Tenes que enviar palabras como array"
      );
    }

    const payloadIA = {
      palabras: normalizadas
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
      res,
      502,
      "No se pudo completar la correccion"
    );
  }
};

// ======================================
// POST /ia/procesar-frase
// ======================================

const procesarFraseConIA = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { palabras, categoria } = req.body || {};

    if (!Array.isArray(palabras)) {
      return responderError(
        res,
        400,
        "Tenes que enviar palabras como array"
      );
    }

    const normalizadas = normalizarPalabras(palabras);

    if (!normalizadas.length) {
      return responderError(
        res,
        400,
        "No hay palabras validas para procesar"
      );
    }

    const categoriaFinal =
      categoria ? String(categoria) : "general";

    // 1. Corregir la frase completa
    const resultadoCorregir = await consultarIA(
      "/corregir",
      { palabras: normalizadas }
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
      typeof resultadoCorregir.data?.frase === "string"
        ? resultadoCorregir.data.frase
        : normalizadas.join(" ");

    // 2. Predecir con las ultimas tres palabras
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
        res,
        502,
        "Error al predecir siguiente palabra con IA",
        resultadoPredecir.data
      );
    }

    // 3. Buscar las imagenes correspondientes
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

    // 5. Enviar respuesta al frontend
    return responderOk(res, {
      frase_original: normalizadas,
      categoria: categoriaFinal,
      frase_corregida: fraseCorregida,

      palabra_base_prediccion:
        ultimasTres[ultimasTres.length - 1],

      predicciones: prediccionesConImagenes
    });

  } catch (error) {
    console.error("Error procesar frase:", error);

    return responderError(
      res,
      502,
      "No se pudo procesar la frase con IA"
    );
  }
};

// ======================================
// EXPORTACIONES
// ======================================

module.exports = {
  pingIA,
  predecirSiguientePalabra,
  corregirFrase,
  procesarFraseConIA,
  buscarPictogramasIA
};
