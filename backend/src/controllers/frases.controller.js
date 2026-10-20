
const supabase = require("../config/Supabase");

// =====================
// HELPERS
// =====================

const responderOk = (res, data, status = 200) => {
  return res.status(status).json({
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

const responderErrorInterno = (res, error) => {
  console.error("Error en frases:", error);

  return responderError(
    res,
    500,
    "Ocurrió un error al procesar la solicitud"
  );
};

const esIdValido = (id) => {
  const numero = Number(id);
  return Number.isSafeInteger(numero) && numero > 0;
};

const guardarHistorial = async (
  id_usuario,
  accion,
  detalle
) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error("Error guardando historial:", error.message);
  }
};

// Busca una frase y comprueba su propietario.
const verificarFrasePropia = async (
  id_frase,
  id_usuario
) => {
  const { data: frase, error } = await supabase
    .from("frases")
    .select("id_frase, id_usuario, texto, fecha_creacion")
    .eq("id_frase", id_frase)
    .maybeSingle();

  if (error) {
    return { error };
  }

  if (!frase) {
    return {
      status: 404,
      mensaje: "Frase no encontrada"
    };
  }

  if (Number(frase.id_usuario) !== Number(id_usuario)) {
    return {
      status: 403,
      mensaje: "No tenés permiso para acceder a esta frase"
    };
  }

  return { frase };
};

// =====================
// POST /frases/armar
// =====================

const armarFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { pictogramas } = req.body || {};

    if (!Array.isArray(pictogramas) || pictogramas.length === 0) {
      return responderError(
        res,
        400,
        "Tenés que enviar al menos un pictograma"
      );
    }

    if (!pictogramas.every(esIdValido)) {
      return responderError(
        res,
        400,
        "Todos los IDs de pictogramas deben ser válidos"
      );
    }

    // Convertimos los IDs a números para evitar problemas
    // al comparar strings con números.
    const ids = pictogramas.map(Number);
    const idsUnicos = [...new Set(ids)];

    const { data: pictogramasData, error: pictogramasError } =
      await supabase
        .from("pictogramas")
        .select(`
          id_pictogramas,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        `)
        .in("id_pictogramas", idsUnicos);

    if (pictogramasError) {
      return responderErrorInterno(res, pictogramasError);
    }

    if (pictogramasData.length !== idsUnicos.length) {
      return responderError(
        res,
        404,
        "Uno o más pictogramas no existen"
      );
    }

    // Verificamos la pertenencia de los personalizados.
    const idsPersonalizados = pictogramasData
      .filter((p) => p.es_personalizado)
      .map((p) => Number(p.id_pictogramas));

    if (idsPersonalizados.length > 0) {
      const { data: asociaciones, error: asociacionesError } =
        await supabase
          .from("usuarios_pictogramas")
          .select("id_pictogramas")
          .eq("id_usuario", id_usuario)
          .in("id_pictogramas", idsPersonalizados);

      if (asociacionesError) {
        return responderErrorInterno(res, asociacionesError);
      }

      const permitidos = new Set(
        asociaciones.map((a) => Number(a.id_pictogramas))
      );

      const sinPermiso = idsPersonalizados.some(
        (id) => !permitidos.has(id)
      );

      if (sinPermiso) {
        return responderError(
          res,
          403,
          "No tenés permiso para usar uno de los pictogramas"
        );
      }
    }

    const pictogramasPorId = new Map(
      pictogramasData.map((p) => [
        Number(p.id_pictogramas),
        p
      ])
    );

    // Respetamos el orden original e IDs repetidos.
    const pictogramasOrdenados = ids.map(
      (id) => pictogramasPorId.get(id)
    );

    const texto = pictogramasOrdenados
      .map((p) => p.nombre)
      .join(" ");

    // Crear frase.
    const { data: fraseCreada, error: fraseError } =
      await supabase
        .from("frases")
        .insert([{ id_usuario, texto }])
        .select()
        .single();

    if (fraseError) {
      return responderErrorInterno(res, fraseError);
    }

    const relaciones = pictogramasOrdenados.map(
      (pictograma, index) => ({
        id_frase: fraseCreada.id_frase,
        id_pictogramas: pictograma.id_pictogramas,
        orden: index + 1
      })
    );

    const { error: relacionesError } = await supabase
      .from("frase_pictogramas")
      .insert(relaciones);

    if (relacionesError) {
      // Intentamos revertir la frase recién creada.
      // Esta compensación no reemplaza una transacción SQL.
      const { error: limpiezaError } = await supabase
        .from("frases")
        .delete()
        .eq("id_frase", fraseCreada.id_frase)
        .eq("id_usuario", id_usuario);

      if (limpiezaError) {
        console.error(
          "No se pudo revertir la frase:",
          limpiezaError.message
        );
      }

      return responderErrorInterno(res, relacionesError);
    }

    await guardarHistorial(
      id_usuario,
      "armar_frase",
      texto
    );

    // Conservamos los campos originales de cada
    // pictograma que recibía el frontend.
    const pictogramasRespuesta = pictogramasOrdenados.map(
      ({ id_pictogramas, nombre, imagen_url, audio_url }) => ({
        id_pictogramas,
        nombre,
        imagen_url,
        audio_url
      })
    );

    return responderOk(res, {
      id_frase: fraseCreada.id_frase,
      id_usuario,
      texto,
      pictogramas: pictogramasRespuesta
    });

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================
// GET /frases/mis-frases
// =====================

const obtenerMisFrases = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: frases, error } = await supabase
      .from("frases")
      .select(`
        id_frase,
        id_usuario,
        texto,
        fecha_creacion,
        frase_pictogramas (
          id_frase_pictogramas,
          orden,
          pictogramas (
            id_pictogramas,
            nombre,
            imagen_url,
            audio_url
          )
        )
      `)
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (error) {
      return responderErrorInterno(res, error);
    }

    const frasesOrdenadas = frases.map((frase) => ({
      ...frase,
      frase_pictogramas: [
        ...(frase.frase_pictogramas || [])
      ].sort((a, b) => a.orden - b.orden)
    }));

    return responderOk(res, frasesOrdenadas);

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================
// GET /frases/:id_frase
// =====================

const obtenerFrasePorId = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_frase } = req.params;

    if (!esIdValido(id_frase)) {
      return responderError(res, 400, "ID de frase inválido");
    }

    const verificacion = await verificarFrasePropia(
      id_frase,
      id_usuario
    );

    if (verificacion.error) {
      return responderErrorInterno(res, verificacion.error);
    }

    if (verificacion.mensaje) {
      return responderError(
        res,
        verificacion.status,
        verificacion.mensaje
      );
    }

    const { data: relaciones, error } = await supabase
      .from("frase_pictogramas")
      .select(`
        id_frase_pictogramas,
        id_frase,
        id_pictogramas,
        orden,
        pictogramas (
          id_pictogramas,
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        )
      `)
      .eq("id_frase", id_frase)
      .order("orden", { ascending: true });

    if (error) {
      return responderErrorInterno(res, error);
    }

    const pictogramasFormateados = relaciones.map(
      (item) => ({
        id_frase_pictograma: item.id_frase_pictogramas,
        id_pictogramas: item.id_pictogramas,
        orden: item.orden,
        ...(item.pictogramas || {})
      })
    );

    return responderOk(res, {
      ...verificacion.frase,
      pictogramas: pictogramasFormateados
    });

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================
// DELETE /frases/:id_frase
// =====================

const eliminarFrase = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_frase } = req.params;

    if (!esIdValido(id_frase)) {
      return responderError(res, 400, "ID de frase inválido");
    }

    const verificacion = await verificarFrasePropia(
      id_frase,
      id_usuario
    );

    if (verificacion.error) {
      return responderErrorInterno(res, verificacion.error);
    }

    if (verificacion.mensaje) {
      return responderError(
        res,
        verificacion.status,
        verificacion.mensaje
      );
    }

    // Conservamos el orden original de borrado.
    const { error: audiosError } = await supabase
      .from("audios")
      .delete()
      .eq("id_frase", id_frase);

    if (audiosError) {
      return responderErrorInterno(res, audiosError);
    }

    const { error: relacionesError } = await supabase
      .from("frase_pictogramas")
      .delete()
      .eq("id_frase", id_frase);

    if (relacionesError) {
      return responderErrorInterno(res, relacionesError);
    }

    const { data: eliminada, error: eliminarError } =
      await supabase
        .from("frases")
        .delete()
        .eq("id_frase", id_frase)
        .eq("id_usuario", id_usuario)
        .select("id_frase")
        .maybeSingle();

    if (eliminarError) {
      return responderErrorInterno(res, eliminarError);
    }

    if (!eliminada) {
      return responderError(
        res,
        404,
        "Frase no encontrada o sin permisos"
      );
    }

    await guardarHistorial(
      id_usuario,
      "eliminar_frase",
      `Frase eliminada: ${verificacion.frase.texto}`
    );

    return responderOk(res, {
      mensaje: "Frase eliminada correctamente"
    });

  } catch (error) {
    return responderErrorInterno(res, error);
  }
};

// =====================
// EXPORTS
// =====================

module.exports = {
  armarFrase,
  obtenerMisFrases,
  obtenerFrasePorId,
  eliminarFrase
};
