const supabase = require("../config/Supabase");

// POST /audios
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
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: id_frase o audio_url"
      });
    }

    // Verifico que la frase exista y sea del usuario logueado
    const { data: frase, error: fraseError } = await supabase
      .from("frases")
      .select("id_frase, id_usuario, texto")
      .eq("id_frase", id_frase)
      .maybeSingle();

    if (fraseError) {
      return res.status(500).json({
        data: null,
        error: fraseError.message
      });
    }

    if (!frase) {
      return res.status(404).json({
        data: null,
        error: "Frase no encontrada"
      });
    }

    if (frase.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para asociar audio a esta frase"
      });
    }

    const { data: audioCreado, error: audioError } = await supabase
      .from("audios")
      .insert([
        {
          id_frase,
          audio_url,
          texto: texto || frase.texto,
          origen: origen || "mock"
        }
      ])
      .select()
      .single();

    if (audioError) {
      return res.status(500).json({
        data: null,
        error: audioError.message
      });
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
    return res.status(500).json({
      data: null,
      error: error.message
    });
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
      return res.status(500).json({
        data: null,
        error: frasesError.message
      });
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
        fecha,
        frases (
          id_frase,
          texto,
          id_usuario
        )
      `)
      .in("id_frase", idsFrases)
      .order("fecha", { ascending: false });

    if (audiosError) {
      return res.status(500).json({
        data: null,
        error: audiosError.message
      });
    }

    return res.json({
      data: audios,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /audios/frase/:id_frase
const obtenerAudioPorFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_frase } = req.params;

    const { data: frase, error: fraseError } = await supabase
      .from("frases")
      .select("id_frase, id_usuario, texto")
      .eq("id_frase", id_frase)
      .maybeSingle();

    if (fraseError) {
      return res.status(500).json({
        data: null,
        error: fraseError.message
      });
    }

    if (!frase) {
      return res.status(404).json({
        data: null,
        error: "Frase no encontrada"
      });
    }

    if (frase.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para ver audios de esta frase"
      });
    }

    const { data: audios, error: audiosError } = await supabase
      .from("audios")
      .select("id_audio, id_frase, audio_url, texto, origen, fecha")
      .eq("id_frase", id_frase)
      .order("fecha", { ascending: false });

    if (audiosError) {
      return res.status(500).json({
        data: null,
        error: audiosError.message
      });
    }

    return res.json({
      data: audios,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
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
        frases (
          id_frase,
          id_usuario,
          texto
        )
      `)
      .eq("id_audio", id_audio)
      .maybeSingle();

    if (audioBuscarError) {
      return res.status(500).json({
        data: null,
        error: audioBuscarError.message
      });
    }

    if (!audio) {
      return res.status(404).json({
        data: null,
        error: "Audio no encontrado"
      });
    }

    if (!audio.frases || audio.frases.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para borrar este audio"
      });
    }

    const { error: borrarError } = await supabase
      .from("audios")
      .delete()
      .eq("id_audio", id_audio);

    if (borrarError) {
      return res.status(500).json({
        data: null,
        error: borrarError.message
      });
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
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

module.exports = {
  crearAudio,
  obtenerMisAudios,
  obtenerAudioPorFrase,
  eliminarAudio
};