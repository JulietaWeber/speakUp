const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");

const SELECT_AUDIO = `
  id_audio,
  id_frase,
  audio_url,
  texto,
  origen,
  fecha_generacion
`;

const responderError = (res, status, error) => {
  return res.status(status).json({
    data: null,
    error
  });
};

const normalizarTexto = (texto) => {
  return String(texto || "").trim();
};

const obtenerFrasePropia = async (id_frase, id_usuario) => {
  const { data: frase, error } = await supabase
    .from("frases")
    .select("id_frase, id_usuario, texto")
    .eq("id_frase", id_frase)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  if (!frase) {
    return {
      frase: null,
      error: "Frase no encontrada"
    };
  }

  if (Number(frase.id_usuario) !== Number(id_usuario)) {
    return {
      frase: null,
      error: "No tenés permiso para usar esta frase"
    };
  }

  return {
    frase,
    error: null
  };
};

const generarAudioElevenLabs = async (texto) => {
  const apiKey = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;
  const modelId = process.env.ELEVENLABS_MODEL_ID || "eleven_multilingual_v2";

  if (!apiKey) {
    throw new Error("Falta configurar ELEVENLABS_API_KEY");
  }

  if (!voiceId) {
    throw new Error("Falta configurar ELEVENLABS_VOICE_ID");
  }

  const url = `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}?output_format=mp3_44100_128`;

  const respuesta = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
      "Content-Type": "application/json",
      "Accept": "audio/mpeg"
    },
    body: JSON.stringify({
      text: texto,
      model_id: modelId,
      voice_settings: {
        stability: 0.5,
        similarity_boost: 0.75
      }
    })
  });

  if (!respuesta.ok) {
    const errorTexto = await respuesta.text();
    throw new Error(`Error ElevenLabs: ${respuesta.status} - ${errorTexto}`);
  }

  const arrayBuffer = await respuesta.arrayBuffer();
  return Buffer.from(arrayBuffer);
};

const subirAudioStorage = async ({ audioBuffer, id_usuario, id_frase }) => {
  const nombreArchivo = `audio-${id_usuario}-${id_frase}-${Date.now()}.mp3`;
  const rutaArchivo = `${id_usuario}/${nombreArchivo}`;

  const { error: uploadError } = await supabaseAdmin.storage
    .from("audios")
    .upload(rutaArchivo, audioBuffer, {
      contentType: "audio/mpeg",
      upsert: true
    });

  if (uploadError) {
    throw new Error(uploadError.message);
  }

  const { data: publicUrlData } = supabaseAdmin.storage
    .from("audios")
    .getPublicUrl(rutaArchivo);

  return publicUrlData.publicUrl;
};

// POST /audios
// Crea un audio manual/mock usando una audio_url ya existente
const crearAudio = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_frase,
      audio_url,
      texto,
      origen
    } = req.body;

    if (!id_frase || !audio_url) {
      return responderError(res, 400, "Faltan datos obligatorios: id_frase o audio_url");
    }

    const resultadoFrase = await obtenerFrasePropia(id_frase, id_usuario);

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.error === "Frase no encontrada" ? 404 : 403,
        resultadoFrase.error
      );
    }

    const frase = resultadoFrase.frase;
    const textoFinal = normalizarTexto(texto) || frase.texto;

    const { data: audioCreado, error: audioError } = await supabase
      .from("audios")
      .insert([
        {
          id_frase,
          audio_url,
          texto: textoFinal,
          origen: origen || "manual"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (audioError) {
      return responderError(res, 500, audioError.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_audio",
        detalle: `Audio creado para frase: ${frase.texto}`
      }
    ]);

    return res.status(201).json({
      data: audioCreado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// POST /audios/generar
// Genera audio real con ElevenLabs, lo sube a Supabase Storage y guarda audio_url
const generarAudioConElevenLabs = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_frase,
      texto
    } = req.body;

    if (!id_frase) {
      return responderError(res, 400, "Falta el id_frase");
    }

    const resultadoFrase = await obtenerFrasePropia(id_frase, id_usuario);

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.error === "Frase no encontrada" ? 404 : 403,
        resultadoFrase.error
      );
    }

    const frase = resultadoFrase.frase;
    const textoFinal = normalizarTexto(texto) || frase.texto;

    if (!textoFinal) {
      return responderError(res, 400, "No hay texto para generar el audio");
    }

    const audioBuffer = await generarAudioElevenLabs(textoFinal);

    const audio_url = await subirAudioStorage({
      audioBuffer,
      id_usuario,
      id_frase
    });

    const { data: audioCreado, error: audioError } = await supabase
      .from("audios")
      .insert([
        {
          id_frase,
          audio_url,
          texto: textoFinal,
          origen: "elevenlabs"
        }
      ])
      .select(SELECT_AUDIO)
      .single();

    if (audioError) {
      return responderError(res, 500, audioError.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "generar_audio_elevenlabs",
        detalle: `Audio generado con ElevenLabs para frase: ${textoFinal}`
      }
    ]);

    return res.status(201).json({
      data: audioCreado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /audios/mis-audios
const obtenerMisAudios = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: frases, error: frasesError } = await supabase
      .from("frases")
      .select("id_frase")
      .eq("id_usuario", id_usuario);

    if (frasesError) {
      return responderError(res, 500, frasesError.message);
    }

    if (!frases || frases.length === 0) {
      return res.json({
        data: [],
        error: null
      });
    }

    const idsFrases = frases.map((frase) => frase.id_frase);

    const { data: audios, error: audiosError } = await supabase
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
      .order("fecha_generacion", { ascending: false });

    if (audiosError) {
      return responderError(res, 500, audiosError.message);
    }

    return res.json({
      data: audios,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /audios/frase/:id_frase
const obtenerAudioPorFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_frase } = req.params;

    const resultadoFrase = await obtenerFrasePropia(id_frase, id_usuario);

    if (resultadoFrase.error) {
      return responderError(
        res,
        resultadoFrase.error === "Frase no encontrada" ? 404 : 403,
        resultadoFrase.error
      );
    }

    const { data: audios, error: audiosError } = await supabase
      .from("audios")
      .select(SELECT_AUDIO)
      .eq("id_frase", id_frase)
      .order("fecha_generacion", { ascending: false });

    if (audiosError) {
      return responderError(res, 500, audiosError.message);
    }

    return res.json({
      data: audios,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// DELETE /audios/:id_audio
const eliminarAudio = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_audio } = req.params;

    const { data: audio, error: audioBuscarError } = await supabase
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
      return responderError(res, 500, audioBuscarError.message);
    }

    if (!audio) {
      return responderError(res, 404, "Audio no encontrado");
    }

    if (!audio.frases || Number(audio.frases.id_usuario) !== Number(id_usuario)) {
      return responderError(res, 403, "No tenés permiso para borrar este audio");
    }

    const { error: borrarError } = await supabase
      .from("audios")
      .delete()
      .eq("id_audio", id_audio);

    if (borrarError) {
      return responderError(res, 500, borrarError.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "eliminar_audio",
        detalle: `Audio eliminado para frase: ${audio.frases.texto}`
      }
    ]);

    return res.json({
      data: {
        mensaje: "Audio eliminado correctamente"
      },
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

module.exports = {
  crearAudio,
  generarAudioConElevenLabs,
  obtenerMisAudios,
  obtenerAudioPorFrase,
  eliminarAudio
};