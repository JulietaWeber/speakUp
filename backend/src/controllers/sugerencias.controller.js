
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

const responderError = (res, status, mensaje) => {
  return res.status(status).json({
    data: null,
    error: mensaje
  });
};

const errorInterno = (res, error) => {
  console.error("Error en sugerencias:", error);

  return responderError(
    res,
    500,
    "Ocurrió un error al procesar las sugerencias"
  );
};

const CAMPOS_PICTOGRAMA =
  "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado";

const normalizarIds = (entrada) => {
  if (!Array.isArray(entrada)) {
    return [];
  }

  return entrada
    .map(Number)
    .filter(
      (id) =>
        Number.isSafeInteger(id) &&
        id > 0
    );
};

const guardarSugerencias = async ({
  id_usuario,
  texto_actual,
  sugerencias,
  origen
}) => {
  const { error } = await supabase
    .from("sugerencias_ia")
    .insert([
      {
        id_usuario,
        texto_actual,
        sugerencia: JSON.stringify(sugerencias),
        origen
      }
    ]);

  if (error) {
    console.error(
      "No se pudieron guardar las sugerencias:",
      error.message
    );
  }
};

// =====================================
// POST /sugerencias
// =====================================

const obtenerSugerencias = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      texto_actual,
      pictogramas_actuales
    } = req.body || {};

    const textoActual =
      typeof texto_actual === "string"
        ? texto_actual
        : "";

    const pictogramasActuales = new Set(
      normalizarIds(pictogramas_actuales)
    );

    // =====================================
    // BUSCAR FRASES DEL USUARIO
    // =====================================

    const {
      data: frasesUsuario,
      error: frasesError
    } = await supabase
      .from("frases")
      .select("id_frase")
      .eq("id_usuario", id_usuario);

    if (frasesError) {
      return errorInterno(res, frasesError);
    }

    // =====================================
    // FALLBACK: SIN HISTORIAL
    // =====================================

    if (
      !frasesUsuario ||
      frasesUsuario.length === 0
    ) {
      const {
        data: pictogramasGenerales,
        error: pictogramasError
      } = await supabase
        .from("pictogramas")
        .select(CAMPOS_PICTOGRAMA)
        .eq("es_personalizado", false)
        .order("id_pictogramas", {
          ascending: true
        })
        .limit(5);

      if (pictogramasError) {
        return errorInterno(
          res,
          pictogramasError
        );
      }

      const sugerencias =
        pictogramasGenerales || [];

      await guardarSugerencias({
        id_usuario,
        texto_actual: textoActual,
        sugerencias,
        origen: "fallback"
      });

      return responderOk(res, {
        texto_actual: textoActual,
        sugerencias,
        mensaje:
          "Sugerencias generales por falta de historial"
      });
    }

    // =====================================
    // CONTAR PICTOGRAMAS USADOS
    // =====================================

    const idsFrases = frasesUsuario.map(
      (frase) => frase.id_frase
    );

    const {
      data: usosPictogramas,
      error: usosError
    } = await supabase
      .from("frase_pictogramas")
      .select("id_pictogramas")
      .in("id_frase", idsFrases);

    if (usosError) {
      return errorInterno(res, usosError);
    }

    const contador = {};

    for (const uso of usosPictogramas || []) {
      const idPicto = Number(
        uso.id_pictogramas
      );

      if (
        !Number.isSafeInteger(idPicto) ||
        pictogramasActuales.has(idPicto)
      ) {
        continue;
      }

      contador[idPicto] =
        (contador[idPicto] || 0) + 1;
    }

    const idsOrdenados = Object.entries(
      contador
    )
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([id]) => Number(id));

    // =====================================
    // SIN SUGERENCIAS
    // =====================================

    if (idsOrdenados.length === 0) {
      return responderOk(res, {
        texto_actual: textoActual,
        sugerencias: [],
        mensaje:
          "No hay sugerencias disponibles"
      });
    }

    // =====================================
    // BUSCAR DATOS DE PICTOGRAMAS
    // =====================================

    const {
      data: pictogramasSugeridos,
      error: pictogramasError
    } = await supabase
      .from("pictogramas")
      .select(CAMPOS_PICTOGRAMA)
      .in("id_pictogramas", idsOrdenados);

    if (pictogramasError) {
      return errorInterno(
        res,
        pictogramasError
      );
    }

    const sugerenciasOrdenadas =
      idsOrdenados
        .map((id) =>
          (pictogramasSugeridos || []).find(
            (p) =>
              Number(p.id_pictogramas) === id
          )
        )
        .filter(Boolean);

    // =====================================
    // GUARDAR HISTORIAL DE SUGERENCIAS
    // =====================================

    await guardarSugerencias({
      id_usuario,
      texto_actual: textoActual,
      sugerencias: sugerenciasOrdenadas,
      origen: "frecuencia"
    });

    return responderOk(res, {
      texto_actual: textoActual,
      sugerencias: sugerenciasOrdenadas
    });

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// GET /sugerencias/mis-sugerencias
// =====================================

const obtenerMisSugerencias = async (
  req,
  res
) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("sugerencias_ia")
      .select(
        "id_sugerencias, id_usuario, texto_actual, sugerencia, origen, fecha"
      )
      .eq("id_usuario", id_usuario)
      .order("fecha", {
        ascending: false
      });

    if (error) {
      return errorInterno(res, error);
    }

    const sugerenciasParseadas = (
      data || []
    ).map((item) => {
      let sugerencia = [];

      try {
        if (Array.isArray(item.sugerencia)) {
          sugerencia = item.sugerencia;
        } else if (
          typeof item.sugerencia === "string"
        ) {
          sugerencia =
            JSON.parse(item.sugerencia);
        } else if (item.sugerencia != null) {
          sugerencia = item.sugerencia;
        }
      } catch (errorParseo) {
        console.error(
          "Sugerencia con formato inválido:",
          item.id_sugerencias
        );
      }

      return {
        ...item,
        sugerencia
      };
    });

    return responderOk(
      res,
      sugerenciasParseadas
    );

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// EXPORTACIONES
// =====================================

module.exports = {
  obtenerSugerencias,
  obtenerMisSugerencias
};
