
const crypto = require("crypto");
const supabase = require("../config/SupabaseAdmin");

const {
  obtenerVocesPublicas,
  obtenerVoiceIdPorVoz,
  VOZ_DEFAULT
} = require("../config/voces");

const BUCKET = "audios";
const DURACION_URL = 15 * 60;

const SELECT_AUDIO = `
  id_audio,
  id_frase,
  audio_url,
  texto,
  origen,
  fecha_generacion
`;

// =====================================
// RESPUESTAS Y VALIDACIONES
// =====================================

const responderOk = (res, data, status = 200) =>
  res.status(status).json({
    data,
    error: null
  });

const responderError = (res, status, mensaje) =>
  res.status(status).json({
    data: null,
    error: mensaje
  });

const errorInterno = (res, error) => {
  console.error("Error en audios:", error);

  return responderError(
    res,
    500,
    "Ocurrió un error al procesar el audio"
  );
};

const normalizarTexto = (texto) =>
  typeof texto === "string"
    ? texto.trim()
    : "";

const idValido = (valor) => {
  if (
    valor === null ||
    valor === undefined ||
    valor === ""
  ) {
    return false;
  }

  const numero = Number(valor);

  return (
    Number.isSafeInteger(numero) &&
    numero > 0
  );
};

// =====================================
// VERIFICAR PROPIEDAD DE FRASE
// =====================================

const obtenerFrasePropia = async (
  id_frase,
  id_usuario
) => {
  if (!idValido(id_frase)) {
    return {
      frase: null,
      status: 400,
      error: "ID de frase inválido"
    };
  }

  const { data: frase, error } = await supabase
    .from("frases")
    .select("id_frase, id_usuario, texto")
    .eq("id_frase", id_frase)
    .maybeSingle();

  if (error) throw error;

  if (!frase) {
    return {
      frase: null,
      status: 404,
      error: "Frase no encontrada"
    };
  }

  if (
    Number(frase.id_usuario) !==
    Number(id_usuario)
  ) {
    return {
      frase: null,
      status: 403,
      error: "No tenés permiso para usar esta frase"
    };
  }

  return {
    frase,
    status: 200,
    error: null
  };
};

// =====================================
// VOZ PREFERIDA
// =====================================

const obtenerUsuarioConVoz = async (id_usuario) => {
  const { data, error } = await supabase
    .from("usuarios")
    .select("id_usuario, voz_preferida")
    .eq("id_usuario", id_usuario)
    .maybeSingle();

  if (error) throw error;

  return data;
};

// =====================================
// STORAGE: IDENTIFICAR ARCHIVOS
// =====================================

// Reconoce las URLs públicas antiguas de
// Supabase y obtiene la ruta del archivo.
//
// Ejemplo:
// https://...supabase.co/storage/v1/object/public/
// audios/6/audio-6-294-123.mp3
//
// Resultado:
// 6/audio-6-294-123.mp3

const obtenerRutaStorage = (audio_url) => {
  if (
    typeof audio_url !== "string" ||
    !audio_url.trim()
  ) {
    return null;
  }

  try {
    const url = new URL(audio_url);
    const supabaseUrl = new URL(
      process.env.SUPABASE_URL
    );

    // No interpretar URLs de otros servidores
    // como archivos de nuestro Storage.
    if (url.origin !== supabaseUrl.origin) {
      return null;
    }

    const prefijos = [
      `/storage/v1/object/public/${BUCKET}/`,
      `/storage/v1/object/sign/${BUCKET}/`,
      `/storage/v1/object/authenticated/${BUCKET}/`
    ];

    const prefijo = prefijos.find((p) =>
      url.pathname.startsWith(p)
    );

    if (!prefijo) return null;

    const ruta = decodeURIComponent(
      url.pathname.slice(prefijo.length)
    );

    if (
      !ruta ||
      ruta.startsWith("/") ||
      ruta.includes("\\") ||
      ruta.split("/").some(
        (parte) =>
          parte === "" ||
          parte === "." ||
          parte === ".."
      )
    ) {
      return null;
    }

    return ruta;

  } catch {
    return null;
  }
};

// =====================================
// STORAGE: URL FIRMADA
// =====================================

const generarUrlFirmada = async (
  rutaArchivo,
  id_usuario
) => {
  // Los audios creados por el backend se
  // guardan dentro de la carpeta del usuario.
  const carpetaUsuario = `${id_usuario}/`;

  if (
    !rutaArchivo.startsWith(carpetaUsuario)
  ) {
    throw new Error(
      "La ruta del audio no pertenece al usuario"
    );
  }

  const { data, error } = await supabase.storage
    .from(BUCKET)
    .createSignedUrl(
      rutaArchivo,
      DURACION_URL
    );

  if (error) throw error;

  if (!data?.signedUrl) {
    throw new Error(
      "No se pudo generar la URL firmada"
    );
  }

  return data.signedUrl;
};

// Sustituye la URL pública guardada en DB
// por una URL firmada para la respuesta.
//
// No modifica el registro en PostgreSQL.

const prepararAudioParaRespuesta = async (
  audio,
  id_usuario
) => {
  const ruta = obtenerRutaStorage(
    audio.audio_url
  );

  if (ruta) {
    const audio_url = await generarUrlFirmada(
      ruta,
      id_usuario
    );

    return {
      ...audio,
      audio_url
    };
  }

  // Si es una URL del bucket de audios pero
  // no pudo interpretarse, NO la exponemos.
  try {
    const url = new URL(audio.audio_url);
    const supabaseUrl = new URL(
      process.env.SUPABASE_URL
    );

    if (
      url.origin === supabaseUrl.origin &&
      url.pathname.includes(
        `/storage/v1/object/`
      )
    ) {
      throw new Error(
        "URL de Storage no reconocida"
      );
    }
  } catch (error) {
    if (
      error.message ===
      "URL de Storage no reconocida"
    ) {
      throw error;
    }

    // Un valor no reconocido no debe exponerse
    // como una dirección de Storage privada.
    if (audio.origen === "elevenlabs") {
      throw new Error(
        "URL de audio ElevenLabs inválida"
      );
    }
  }

  // Compatibilidad con audios manuales
  // alojados fuera de nuestro bucket.
  return audio;
};

const prepararListaAudios = async (
  audios,
  id_usuario
) =>
  Promise.all(
    (audios || []).map((audio) =>
      prepararAudioParaRespuesta(
        audio,
        id_usuario
      )
    )
  );

// =====================================
// STORAGE: SUBIR ARCHIVO
// =====================================

const subirAudioStorage = async ({
  audioBuffer,
  id_usuario,
  id_frase
}) => {
  const nombreArchivo =
    `audio-${id_usuario}-${id_frase}-` +
    `${crypto.randomUUID()}.mp3`;

  const rutaArchivo =
    `${id_usuario}/${nombreArchivo}`;

  const { error: uploadError } =
    await supabase.storage
      .from(BUCKET)
      .upload(
        rutaArchivo,
        audioBuffer,
        {
          contentType: "audio/mpeg",
          upsert: false
        }
      );

  if (uploadError) throw uploadError;

  // Generamos primero la URL firmada.
  // Si falla, limpiamos el archivo nuevo.
  let urlFirmada;

  try {
    urlFirmada = await generarUrlFirmada(
      rutaArchivo,
      id_usuario
    );
  } catch (error) {
    await eliminarArchivoStorage(
      rutaArchivo
    );

    throw error;
  }

  // Conservamos el formato de URL pública
  // únicamente como referencia interna en DB.
  // No se envía al frontend.
  const { data: urlData } = supabase.storage
    .from(BUCKET)
    .getPublicUrl(rutaArchivo);

  return {
    rutaArchivo,
    urlGuardada: urlData.publicUrl,
    urlFirmada
  };
};

const eliminarArchivoStorage = async (
  rutaArchivo
) => {
  if (!rutaArchivo) return;

  const { error } = await supabase.storage
    .from(BUCKET)
    .remove([rutaArchivo]);

  if (error) {
    console.error(
      "Error limpiando archivo de audio:",
      error.message
    );
  }
};

// =====================================
// HISTORIAL
// =====================================

const registrarHistorial = async (
  id_usuario,
  accion,
  detalle
) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([
      {
        id_usuario,
        accion,
        detalle
      }
    ]);

  if (error) {
    console.error(
      "Error registrando historial:",
      error.message
    );
  }
};

// =====================================
// ELEVENLABS
// =====================================

const generarAudioElevenLabs = async (
  texto,
  voiceId
) => {
  const apiKey =
    process.env.ELEVENLABS_API_KEY;

  const modelId =
    process.env.ELEVENLABS_MODEL_ID ||
    "eleven_multilingual_v2";

  if (!apiKey) {
    throw new Error(
      "Falta configurar ELEVENLABS_API_KEY"
    );
  }

  if (!voiceId) {
    throw new Error(
      "No se encontró una voz válida"
    );
  }

  const url =
    `https://api.elevenlabs.io/v1/text-to-speech/` +
    `${encodeURIComponent(voiceId)}` +
    `?output_format=mp3_44100_128`;

  const respuesta = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
      "Content-Type": "application/json",
      Accept: "audio/mpeg"
    },
    body: JSON.stringify({
      text: texto,
      model_id: modelId,
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75
      }
    }),
    signal: AbortSignal.timeout(60000)
  });

  if (!respuesta.ok) {
    console.error(
      "ElevenLabs devolvió:",
      respuesta.status
    );

    throw new Error(
      "No se pudo generar el audio con ElevenLabs"
    );
  }

  const arrayBuffer =
    await respuesta.arrayBuffer();

  return Buffer.from(arrayBuffer);
};

// =====================================
// GET /audios/voces
// =====================================

const obtenerVocesDisponibles = async (
  req,
  res
) => {
  try {
    return responderOk(
      res,
      obtenerVocesPublicas()
    );
  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// POST /audios
// CREACIÓN MANUAL
// =====================================

const crearAudio = async (req, res) => {
  try {
    const id_usuario =
      req.usuario.id_usuario;

    const {
      id_frase,
      audio_url,
      texto,
      origen
    } = req.body || {};

    if (!idValido(id_frase)) {
      return responderError(
        res,
        400,
        "ID de frase inválido"
      );
    }

    if (
      typeof audio_url !== "string" ||
      !audio_url.trim()
    ) {
      return responderError(
        res,
        400,
        "Falta audio_url"
      );
    }

    let urlManual;

    try {
      urlManual = new URL(audio_url.trim());

      if (
        !["https:", "http:"].includes(
          urlManual.protocol
        )
      ) {
        throw new Error("Protocolo inválido");
      }
    } catch {
      return responderError(
        res,
        400,
        "audio_url debe ser una URL válida"
      );
    }

    // Un usuario no puede registrar una URL
    // privada de nuestro Storage y luego
    // pedir que el backend se la firme.
    const origenSupabase = new URL(
      process.env.SUPABASE_URL
    ).origin;

    if (
      urlManual.origin === origenSupabase &&
      urlManual.pathname.startsWith(
        "/storage/v1/object/"
      )
    ) {
      return responderError(
        res,
        403,
        "No se pueden registrar archivos internos de Storage mediante esta ruta"
      );
    }

    const resultadoFrase =
      await obtenerFrasePropia(
        id_frase,
        id_usuario
      );

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.status,
        resultadoFrase.error
      );
    }

    const frase = resultadoFrase.frase;

    const textoFinal =
      normalizarTexto(texto) ||
      frase.texto;

    const {
      data: audioCreado,
      error
    } = await supabase
      .from("audios")
      .insert([
        {
          id_frase: frase.id_frase,
          audio_url: urlManual.toString(),
          texto: textoFinal,
          origen: origen || "manual"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (error) {
      return errorInterno(res, error);
    }

    await registrarHistorial(
      id_usuario,
      "crear_audio",
      `Audio creado para frase: ${frase.texto}`
    );

    return responderOk(
      res,
      audioCreado,
      201
    );

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// POST /audios/generar
// =====================================

const generarAudioConElevenLabs = async (
  req,
  res
) => {
  let archivoNuevo = null;
  let registroCreado = false;

  try {
    const id_usuario =
      req.usuario.id_usuario;

    const {
      id_frase,
      texto
    } = req.body || {};

    if (!idValido(id_frase)) {
      return responderError(
        res,
        400,
        "ID de frase inválido"
      );
    }

    const resultadoFrase =
      await obtenerFrasePropia(
        id_frase,
        id_usuario
      );

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.status,
        resultadoFrase.error
      );
    }

    const frase = resultadoFrase.frase;

    const textoFinal =
      normalizarTexto(texto) ||
      frase.texto;

    if (!textoFinal) {
      return responderError(
        res,
        400,
        "No hay texto para generar el audio"
      );
    }

    const usuario =
      await obtenerUsuarioConVoz(
        id_usuario
      );

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado"
      );
    }

    const vozPreferida =
      usuario.voz_preferida ||
      VOZ_DEFAULT;

    const voiceId =
      obtenerVoiceIdPorVoz(
        vozPreferida
      );

    const audioBuffer =
      await generarAudioElevenLabs(
        textoFinal,
        voiceId
      );

    archivoNuevo =
      await subirAudioStorage({
        audioBuffer,
        id_usuario,
        id_frase
      });

    const {
      data: audioCreado,
      error: audioError
    } = await supabase
      .from("audios")
      .insert([
        {
          id_frase: frase.id_frase,
          audio_url:
            archivoNuevo.urlGuardada,
          texto: textoFinal,
          origen: "elevenlabs"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (audioError) {
      return errorInterno(
        res,
        audioError
      );
    }

    registroCreado = true;

    await registrarHistorial(
      id_usuario,
      "generar_audio_elevenlabs",
      `Audio generado para frase: ${textoFinal}. Voz: ${vozPreferida}`
    );

    return responderOk(
      res,
      {
        ...audioCreado,
        audio_url:
          archivoNuevo.urlFirmada,
        voz_usada: vozPreferida
      },
      201
    );

  } catch (error) {
    return errorInterno(res, error);

  } finally {
    // Solo limpiar si NO se guardó el
    // registro en la base de datos.
    if (
      archivoNuevo &&
      !registroCreado
    ) {
      await eliminarArchivoStorage(
        archivoNuevo.rutaArchivo
      );
    }
  }
};

// =====================================
// GET /audios/mis-audios
// =====================================

const obtenerMisAudios = async (
  req,
  res
) => {
  try {
    const id_usuario =
      req.usuario.id_usuario;

    const {
      data: frases,
      error: frasesError
    } = await supabase
      .from("frases")
      .select("id_frase")
      .eq("id_usuario", id_usuario);

    if (frasesError) {
      return errorInterno(
        res,
        frasesError
      );
    }

    if (
      !frases ||
      frases.length === 0
    ) {
      return responderOk(res, []);
    }

    const idsFrases = frases.map(
      (frase) => frase.id_frase
    );

    const {
      data: audios,
      error: audiosError
    } = await supabase
      .from("audios")
      .select(`
        id_audio,
        id_frase,
        audio_url,
        texto,
        origen,
        fecha_generacion,
        frases (
          id_frase,
          texto,
          id_usuario
        )
      `)
      .in("id_frase", idsFrases)
      .order(
        "fecha_generacion",
        { ascending: false }
      );

    if (audiosError) {
      return errorInterno(
        res,
        audiosError
      );
    }

    // Se firman solamente los audios
    // que pertenecen a este usuario.
    const audiosSeguros =
      await prepararListaAudios(
        audios,
        id_usuario
      );

    return responderOk(
      res,
      audiosSeguros
    );

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// GET /audios/frase/:id_frase
// =====================================

const obtenerAudioPorFrase = async (
  req,
  res
) => {
  try {
    const id_usuario =
      req.usuario.id_usuario;

    const { id_frase } = req.params;

    const resultadoFrase =
      await obtenerFrasePropia(
        id_frase,
        id_usuario
      );

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.status,
        resultadoFrase.error
      );
    }

    const {
      data: audios,
      error
    } = await supabase
      .from("audios")
      .select(SELECT_AUDIO)
      .eq("id_frase", id_frase)
      .order(
        "fecha_generacion",
        { ascending: false }
      );

    if (error) {
      return errorInterno(res, error);
    }

    const audiosSeguros =
      await prepararListaAudios(
        audios,
        id_usuario
      );

    return responderOk(
      res,
      audiosSeguros
    );

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// DELETE /audios/:id_audio
// =====================================

const eliminarAudio = async (
  req,
  res
) => {
  try {
    const id_usuario =
      req.usuario.id_usuario;

    const { id_audio } = req.params;

    if (!idValido(id_audio)) {
      return responderError(
        res,
        400,
        "ID de audio inválido"
      );
    }

    const {
      data: audio,
      error: buscarError
    } = await supabase
      .from("audios")
      .select(`
        id_audio,
        id_frase,
        audio_url,
        texto,
        origen,
        fecha_generacion,
        frases (
          id_frase,
          id_usuario,
          texto
        )
      `)
      .eq("id_audio", id_audio)
      .maybeSingle();

    if (buscarError) {
      return errorInterno(
        res,
        buscarError
      );
    }

    if (!audio) {
      return responderError(
        res,
        404,
        "Audio no encontrado"
      );
    }

    if (
      !audio.frases ||
      Number(audio.frases.id_usuario) !==
        Number(id_usuario)
    ) {
      return responderError(
        res,
        403,
        "No tenés permiso para borrar este audio"
      );
    }

    const { error: borrarError } =
      await supabase
        .from("audios")
        .delete()
        .eq("id_audio", id_audio)
        .eq("id_frase", audio.id_frase);

    if (borrarError) {
      return errorInterno(
        res,
        borrarError
      );
    }

    await registrarHistorial(
      id_usuario,
      "eliminar_audio",
      `Audio eliminado para frase: ${audio.frases.texto}`
    );

    return responderOk(res, {
      mensaje:
        "Audio eliminado correctamente"
    });

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// EXPORTACIONES
// =====================================

module.exports = {
  crearAudio,
  generarAudioConElevenLabs,
  obtenerMisAudios,
  obtenerAudioPorFrase,
  eliminarAudio,
  obtenerVocesDisponibles
};
