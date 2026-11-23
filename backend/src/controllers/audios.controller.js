
const supabase = require("../config/SupabaseAdmin");

const {
  obtenerVocesPublicas,
  obtenerVoiceIdPorVoz,
  VOZ_DEFAULT
} = require("../config/voces");

const SELECT_AUDIO = `
  id_audio,
  id_frase,
  audio_url,
  texto,
  origen,
  fecha_generacion
`;

// =====================================
// HELPERS
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
  typeof texto === "string" ? texto.trim() : "";

const idValido = (valor) => {
  const numero = Number(valor);

  return (
    valor !== null &&
    valor !== undefined &&
    valor !== "" &&
    Number.isSafeInteger(numero) &&
    numero > 0
  );
};

const registrarHistorial = async (
  id_usuario,
  accion,
  detalle
) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error(
      "Error registrando historial de audio:",
      error.message
    );
  }
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
    Number(frase.id_usuario) !== Number(id_usuario)
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
// USUARIO Y VOZ PREFERIDA
// =====================================

const obtenerUsuarioConVoz = async (id_usuario) => {
  const { data: usuario, error } = await supabase
    .from("usuarios")
    .select("id_usuario, voz_preferida")
    .eq("id_usuario", id_usuario)
    .maybeSingle();

  if (error) throw error;

  return usuario;
};

// =====================================
// ELEVENLABS
// =====================================

const generarAudioElevenLabs = async (
  texto,
  voiceId
) => {
  const apiKey = process.env.ELEVENLABS_API_KEY;

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
      "No se encontró una voz válida para generar el audio"
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
    const errorTexto = await respuesta.text();

    console.error(
      "Error ElevenLabs:",
      respuesta.status,
      errorTexto.slice(0, 500)
    );

    throw new Error(
      "No se pudo generar el audio con ElevenLabs"
    );
  }

  const arrayBuffer = await respuesta.arrayBuffer();

  return Buffer.from(arrayBuffer);
};

// =====================================
// SUPABASE STORAGE
// =====================================

const subirAudioStorage = async ({
  audioBuffer,
  id_usuario,
  id_frase
}) => {
  const crypto = require("crypto");

  const nombreArchivo =
    `audio-${id_usuario}-${id_frase}-` +
    `${crypto.randomUUID()}.mp3`;

  const rutaArchivo =
    `${id_usuario}/${nombreArchivo}`;

  const { error: uploadError } = await supabase.storage
    .from("audios")
    .upload(rutaArchivo, audioBuffer, {
      contentType: "audio/mpeg",
      upsert: false
    });

  if (uploadError) throw uploadError;

  const { data: publicUrlData } = supabase.storage
    .from("audios")
    .getPublicUrl(rutaArchivo);

  return {
    audio_url: publicUrlData.publicUrl,
    rutaArchivo
  };
};

const eliminarArchivoStorage = async (rutaArchivo) => {
  if (!rutaArchivo) return;

  const { error } = await supabase.storage
    .from("audios")
    .remove([rutaArchivo]);

  if (error) {
    console.error(
      "No se pudo limpiar el audio de Storage:",
      error.message
    );
  }
};

// =====================================
// GET /audios/voces
// =====================================

const obtenerVocesDisponibles = async (req, res) => {
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
// CREAR AUDIO MANUAL
// =====================================

const crearAudio = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

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

    const resultadoFrase = await obtenerFrasePropia(
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
      normalizarTexto(texto) || frase.texto;

    const { data: audioCreado, error } = await supabase
      .from("audios")
      .insert([
        {
          id_frase: frase.id_frase,
          audio_url: audio_url.trim(),
          texto: textoFinal,
          origen: origen || "manual"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (error) return errorInterno(res, error);

    await registrarHistorial(
      id_usuario,
      "crear_audio",
      `Audio creado para frase: ${frase.texto}`
    );

    return responderOk(res, audioCreado, 201);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// POST /audios/generar
// =====================================

const generarAudioConElevenLabs = async (req, res) => {
  let archivoNuevo = null;

  try {
    const id_usuario = req.usuario.id_usuario;

    const { id_frase, texto } = req.body || {};

    if (!idValido(id_frase)) {
      return responderError(
        res,
        400,
        "ID de frase inválido"
      );
    }

    const resultadoFrase = await obtenerFrasePropia(
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
      normalizarTexto(texto) || frase.texto;

    if (!textoFinal) {
      return responderError(
        res,
        400,
        "No hay texto para generar el audio"
      );
    }

    const usuario = await obtenerUsuarioConVoz(
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
      usuario.voz_preferida || VOZ_DEFAULT;

    const voiceId = obtenerVoiceIdPorVoz(
      vozPreferida
    );

    const audioBuffer = await generarAudioElevenLabs(
      textoFinal,
      voiceId
    );

    archivoNuevo = await subirAudioStorage({
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
          audio_url: archivoNuevo.audio_url,
          texto: textoFinal,
          origen: "elevenlabs"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (audioError) {
      await eliminarArchivoStorage(
        archivoNuevo.rutaArchivo
      );

      archivoNuevo = null;

      return errorInterno(res, audioError);
    }

    await registrarHistorial(
      id_usuario,
      "generar_audio_elevenlabs",
      `Audio generado con ElevenLabs para frase: ${textoFinal}. Voz usada: ${vozPreferida}`
    );

    return responderOk(
      res,
      {
        ...audioCreado,
        voz_usada: vozPreferida
      },
      201
    );

  } catch (error) {
    if (archivoNuevo) {
      await eliminarArchivoStorage(
        archivoNuevo.rutaArchivo
      );
    }

    return errorInterno(res, error);
  }
};

// =====================================
// GET /audios/mis-audios
// =====================================

const obtenerMisAudios = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      data: frases,
      error: frasesError
    } = await supabase
      .from("frases")
      .select("id_frase")
      .eq("id_usuario", id_usuario);

    if (frasesError) {
      return errorInterno(res, frasesError);
    }

    if (!frases || frases.length === 0) {
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
      return errorInterno(res, audiosError);
    }

    return responderOk(res, audios);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// GET /audios/frase/:id_frase
// =====================================

const obtenerAudioPorFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_frase } = req.params;

    const resultadoFrase = await obtenerFrasePropia(
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

    const { data: audios, error } = await supabase
      .from("audios")
      .select(SELECT_AUDIO)
      .eq("id_frase", id_frase)
      .order(
        "fecha_generacion",
        { ascending: false }
      );

    if (error) return errorInterno(res, error);

    return responderOk(res, audios);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// DELETE /audios/:id_audio
// =====================================

const eliminarAudio = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
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
      error: audioBuscarError
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

    if (audioBuscarError) {
      return errorInterno(res, audioBuscarError);
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

    const { error: borrarError } = await supabase
      .from("audios")
      .delete()
      .eq("id_audio", id_audio)
      .eq("id_frase", audio.id_frase);

    if (borrarError) {
      return errorInterno(res, borrarError);
    }

    await registrarHistorial(
      id_usuario,
      "eliminar_audio",
      `Audio eliminado para frase: ${audio.frases.texto}`
    );

    return responderOk(res, {
      mensaje: "Audio eliminado correctamente"
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
