
const supabase = require("../config/SupabaseAdmin");

// =====================================
// HELPERS
// =====================================

const responderOk = (res, data) => {
  return res.json({
    data,
    error: null
  });
};

const responderErrorInterno = (res, error) => {
  console.error("Error historial de uso:", error);

  return res.status(500).json({
    data: null,
    error: "Ocurrió un error al consultar el historial"
  });
};

// =====================================
// GET /historial-uso/me
// =====================================

const obtenerMiHistorial = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: historial, error } = await supabase
      .from("historial_uso")
      .select(
        "id_historial, id_usuario, accion, detalle, fecha"
      )
      .eq("id_usuario", id_usuario)
      .order("fecha", {
        ascending: false
      });

    if (error) {
      return responderErrorInterno(res, error);
    }

    return responderOk(res, historial || []);

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================================
// GET /historial-uso/resumen
// =====================================

const obtenerResumenHistorial = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    // =====================================
    // 1. FRASES DEL USUARIO
    // =====================================

    const {
      data: frases,
      error: frasesError
    } = await supabase
      .from("frases")
      .select("id_frase, texto, fecha_creacion")
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", {
        ascending: false
      });

    if (frasesError) {
      return responderErrorInterno(
        res,
        frasesError
      );
    }

    const frasesUsuario = frases || [];

    const total_frases = frasesUsuario.length;

    const ultima_frase =
      frasesUsuario.length > 0
        ? frasesUsuario[0].texto
        : null;

    const idsFrases = frasesUsuario.map(
      (frase) => frase.id_frase
    );

    // =====================================
    // 2. PICTOGRAMAS MÁS USADOS
    // =====================================

    let pictogramas_mas_usados = [];

    if (idsFrases.length > 0) {
      const {
        data: usosPictogramas,
        error: usosError
      } = await supabase
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
        return responderErrorInterno(
          res,
          usosError
        );
      }

      const contador = {};

      for (const uso of usosPictogramas || []) {
        const idPicto = uso.id_pictogramas;

        if (!contador[idPicto]) {
          contador[idPicto] = {
            id_pictogramas: idPicto,
            nombre:
              uso.pictogramas?.nombre || null,
            imagen_url:
              uso.pictogramas?.imagen_url || null,
            audio_url:
              uso.pictogramas?.audio_url || null,
            es_personalizado:
              uso.pictogramas?.es_personalizado ||
              false,
            cantidad: 0
          };
        }

        contador[idPicto].cantidad += 1;
      }

      pictogramas_mas_usados =
        Object.values(contador)
          .sort(
            (a, b) =>
              b.cantidad - a.cantidad
          )
          .slice(0, 5);
    }

    // =====================================
    // 3. PICTOGRAMAS PERSONALIZADOS
    // =====================================

    const {
      count: totalPictogramasPersonalizados,
      error: personalizadosError
    } = await supabase
      .from("usuarios_pictogramas")
      .select("*", {
        count: "exact",
        head: true
      })
      .eq("id_usuario", id_usuario);

    if (personalizadosError) {
      return responderErrorInterno(
        res,
        personalizadosError
      );
    }

    // =====================================
    // 4. AUDIOS DEL USUARIO
    // =====================================

    let total_audios = 0;

    if (idsFrases.length > 0) {
      const {
        count: totalAudios,
        error: audiosError
      } = await supabase
        .from("audios")
        .select("*", {
          count: "exact",
          head: true
        })
        .in("id_frase", idsFrases);

      if (audiosError) {
        return responderErrorInterno(
          res,
          audiosError
        );
      }

      total_audios = totalAudios || 0;
    }

    // =====================================
    // 5. SUGERENCIAS DE IA
    // =====================================

    const {
      count: totalSugerencias,
      error: sugerenciasError
    } = await supabase
      .from("sugerencias_ia")
      .select("*", {
        count: "exact",
        head: true
      })
      .eq("id_usuario", id_usuario);

    if (sugerenciasError) {
      return responderErrorInterno(
        res,
        sugerenciasError
      );
    }

    // =====================================
    // RESPUESTA
    // =====================================

    return responderOk(res, {
      total_frases,
      ultima_frase,
      pictogramas_mas_usados,
      total_pictogramas_personalizados:
        totalPictogramasPersonalizados || 0,
      total_audios,
      total_sugerencias:
        totalSugerencias || 0
    });

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================================
// EXPORTACIONES
// =====================================

module.exports = {
  obtenerMiHistorial,
  obtenerResumenHistorial
};
