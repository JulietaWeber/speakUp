const supabase = require("../config/Supabase");

const obtenerSugerencias = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { texto_actual, pictogramas_actuales } = req.body;

    const pictogramasActuales = Array.isArray(pictogramas_actuales)
      ? pictogramas_actuales
      : [];

    const { data: frasesUsuario, error: frasesError } = await supabase
      .from("frases")
      .select("id_frase")
      .eq("id_usuario", id_usuario);

    if (frasesError) {
      return res.status(500).json({
        data: null,
        error: frasesError.message
      });
    }

    if (!frasesUsuario || frasesUsuario.length === 0) {
  const { data: pictogramasGenerales, error: pictogramasGeneralesError } =
    await supabase
      .from("pictogramas")
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .limit(5);

    if (pictogramasGeneralesError) {
      return res.status(500).json({
      data: null,
      error: pictogramasGeneralesError.message
     });
    }

    await supabase.from("sugerencias_ia").insert([
    {
      id_usuario,
      texto_actual: texto_actual || "",
      sugerencia: JSON.stringify(pictogramasGenerales),
      origen: "fallback"
    }
  ]);

  return res.json({
    data: {
      texto_actual: texto_actual || "",
      sugerencias: pictogramasGenerales,
      mensaje: "Sugerencias generales por falta de historial"
    },
    error: null
  });
    }   
    

    const idsFrases = frasesUsuario.map((frase) => frase.id_frase);

    const { data: usosPictogramas, error: usosError } = await supabase
      .from("frase_pictogramas")
      .select("id_pictogramas")
      .in("id_frase", idsFrases);

    if (usosError) {
      return res.status(500).json({
        data: null,
        error: usosError.message
      });
    }

    const contador = {};

    usosPictogramas.forEach((uso) => {
      const idPicto = uso.id_pictogramas;

      if (!pictogramasActuales.includes(idPicto)) {
        contador[idPicto] = (contador[idPicto] || 0) + 1;
      }
    });

    const idsOrdenados = Object.entries(contador)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([id]) => Number(id));

    if (idsOrdenados.length === 0) {
      return res.json({
        data: {
          texto_actual: texto_actual || "",
          sugerencias: [],
          mensaje: "No hay sugerencias disponibles"
        },
        error: null
      });
    }

    const { data: pictogramasSugeridos, error: pictogramasError } =
      await supabase
        .from("pictogramas")
        .select(
          "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
        )
        .in("id_pictogramas", idsOrdenados);

    if (pictogramasError) {
      return res.status(500).json({
        data: null,
        error: pictogramasError.message
      });
    }

    const sugerenciasOrdenadas = idsOrdenados
      .map((id) =>
        pictogramasSugeridos.find((p) => p.id_pictogramas === id)
      )
      .filter(Boolean);

    const { error: guardarError } = await supabase
      .from("sugerencias_ia")
      .insert([
        {
          id_usuario,
          texto_actual: texto_actual || "",
          sugerencia: JSON.stringify(sugerenciasOrdenadas),
          origen: "frecuencia"
        }
      ]);

    if (guardarError) {
      return res.status(500).json({
        data: null,
        error: guardarError.message
      });
    }

    return res.json({
      data: {
        texto_actual: texto_actual || "",
        sugerencias: sugerenciasOrdenadas
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

const obtenerMisSugerencias = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("sugerencias_ia")
      .select(
        "id_sugerencias, id_usuario, texto_actual, sugerencia, origen, fecha"
      )
      .eq("id_usuario", id_usuario)
      .order("fecha", { ascending: false });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    const sugerenciasParseadas = data.map((item) => ({
      ...item,
      sugerencia: item.sugerencia ? JSON.parse(item.sugerencia) : []
    }));

    return res.json({
      data: sugerenciasParseadas,
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
  obtenerSugerencias,
  obtenerMisSugerencias
};