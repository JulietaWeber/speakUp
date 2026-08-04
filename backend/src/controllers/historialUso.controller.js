const supabase = require("../config/Supabase");

// GET /historial-uso/me
const obtenerMiHistorial = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: historial, error } = await supabase
      .from("historial_uso")
      .select("id_historial, id_usuario, accion, detalle, fecha")
      .eq("id_usuario", id_usuario)
      .order("fecha", { ascending: false });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data: historial,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /historial-uso/resumen
const obtenerResumenHistorial = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    // 1. Buscar frases del usuario
    const { data: frases, error: frasesError } = await supabase
      .from("frases")
      .select("id_frase, texto, fecha_creacion")
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (frasesError) {
      return res.status(500).json({
        data: null,
        error: frasesError.message
      });
    }

    const total_frases = frases ? frases.length : 0;
    const ultima_frase = frases && frases.length > 0 ? frases[0].texto : null;

    // 2. Sacar IDs de frases para buscar pictogramas usados
    const idsFrases = frases ? frases.map((frase) => frase.id_frase) : [];

    let pictogramas_mas_usados = [];

    if (idsFrases.length > 0) {
      const { data: usosPictogramas, error: usosError } = await supabase
        .from("frase_pictogramas")
        .select(`
          id_pictogramas,
          pictogramas (
            id_pictogramas,
            nombre,
            imagen_url,
            audio_url,
            es_personalizado
          )
        `)
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

        if (!contador[idPicto]) {
          contador[idPicto] = {
            id_pictogramas: idPicto,
            nombre: uso.pictogramas?.nombre || null,
            imagen_url: uso.pictogramas?.imagen_url || null,
            audio_url: uso.pictogramas?.audio_url || null,
            es_personalizado: uso.pictogramas?.es_personalizado || false,
            cantidad: 0
          };
        }

        contador[idPicto].cantidad += 1;
      });

      pictogramas_mas_usados = Object.values(contador)
        .sort((a, b) => b.cantidad - a.cantidad)
        .slice(0, 5);
    }

    // 3. Total de pictogramas personalizados del usuario
    const { count: totalPictogramasPersonalizados, error: personalizadosError } =
      await supabase
        .from("usuarios_pictogramas")
        .select("*", { count: "exact", head: true })
        .eq("id_usuario", id_usuario);

    if (personalizadosError) {
      return res.status(500).json({
        data: null,
        error: personalizadosError.message
      });
    }

    // 4. Total de audios asociados a frases del usuario
    let total_audios = 0;

    if (idsFrases.length > 0) {
      const { count: totalAudios, error: audiosError } = await supabase
        .from("audios")
        .select("*", { count: "exact", head: true })
        .in("id_frase", idsFrases);

      if (audiosError) {
        return res.status(500).json({
          data: null,
          error: audiosError.message
        });
      }

      total_audios = totalAudios || 0;
    }

    // 5. Total de sugerencias generadas
    const { count: totalSugerencias, error: sugerenciasError } = await supabase
      .from("sugerencias_ia")
      .select("*", { count: "exact", head: true })
      .eq("id_usuario", id_usuario);

    if (sugerenciasError) {
      return res.status(500).json({
        data: null,
        error: sugerenciasError.message
      });
    }

    return res.json({
      data: {
        total_frases,
        ultima_frase,
        pictogramas_mas_usados,
        total_pictogramas_personalizados: totalPictogramasPersonalizados || 0,
        total_audios,
        total_sugerencias: totalSugerencias || 0
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
  obtenerMiHistorial,
  obtenerResumenHistorial
};