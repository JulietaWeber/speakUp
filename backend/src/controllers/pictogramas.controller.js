
const crypto = require("crypto");
const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");

const CAMPOS =
  "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado";

const BUCKET = "pictogramas-imagenes";

// =====================================
// HELPERS
// =====================================

const ok = (res, data, status = 200) =>
  res.status(status).json({ data, error: null });

const fallo = (res, status, error) =>
  res.status(status).json({ data: null, error });

const idValido = (id) =>
  Number.isSafeInteger(Number(id)) && Number(id) > 0;

const normalizar = (valor) =>
  typeof valor === "string" ? valor.trim() : "";

const compararNombre = (nombre) =>
  normalizar(nombre).toLowerCase();

const validarNombre = (nombre) => {
  const limpio = normalizar(nombre);

  if (!limpio) {
    return "El nombre del pictograma no puede estar vacío";
  }

  if (limpio.length < 2) {
    return "El nombre debe tener al menos 2 caracteres";
  }

  if (limpio.length > 50) {
    return "El nombre no puede superar los 50 caracteres";
  }

  if (["poronga", "pete"].includes(compararNombre(limpio))) {
    return "El nombre del pictograma no está permitido";
  }

  return null;
};

const manejarError = (res, error) => {
  console.error("Error pictogramas:", error);
  return fallo(res, 500, "Error interno al procesar el pictograma");
};

const registrarHistorial = async (id_usuario, accion, detalle) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error("Error historial:", error.message);
  }
};

// =====================================
// CATEGORÍAS
// =====================================

const buscarCategoria = async (id_categorias) => {
  const { data, error } = await supabase
    .from("categorias")
    .select("id_categorias, nombre, id_usuario, es_personalizada")
    .eq("id_categorias", id_categorias)
    .maybeSingle();

  if (error) throw error;

  return data;
};

const categoriaGeneral = (categoria) =>
  categoria.id_usuario == null &&
  categoria.es_personalizada === false;

const puedeUsarCategoria = (categoria, id_usuario) =>
  categoriaGeneral(categoria) ||
  Number(categoria.id_usuario) === Number(id_usuario);

const comprobarCategoria = async (
  id_categorias,
  id_usuario,
  personalizado
) => {
  if (!idValido(id_categorias)) {
    return { status: 400, error: "ID de categoría inválido" };
  }

  const categoria = await buscarCategoria(id_categorias);

  if (!categoria) {
    return { status: 404, error: "Categoría no encontrada" };
  }

  if (!personalizado && !categoriaGeneral(categoria)) {
    return {
      status: 403,
      error: "Los pictogramas generales requieren una categoría general"
    };
  }

  if (personalizado && !puedeUsarCategoria(categoria, id_usuario)) {
    return {
      status: 403,
      error: "No tenés permiso para utilizar esta categoría"
    };
  }

  return { categoria };
};

// =====================================
// PROPIEDAD
// =====================================

const buscarPictograma = async (id) => {
  const { data, error } = await supabase
    .from("pictogramas")
    .select(CAMPOS)
    .eq("id_pictogramas", id)
    .maybeSingle();

  if (error) throw error;
  return data;
};

const buscarPersonalizadoPropio = async (
  id_usuario,
  id_pictograma
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select(`id_usuario, id_pictogramas, pictogramas (${CAMPOS})`)
    .eq("id_usuario", id_usuario)
    .eq("id_pictogramas", id_pictograma)
    .maybeSingle();

  if (error) throw error;

  const pictograma = data?.pictogramas;

  return pictograma?.es_personalizado ? pictograma : null;
};

const tieneOtrosUsuarios = async (
  id_pictograma,
  id_usuario
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select("id_usuario")
    .eq("id_pictogramas", id_pictograma)
    .neq("id_usuario", id_usuario)
    .limit(1);

  if (error) throw error;

  return data.length > 0;
};

const estaEnUso = async (id_pictograma) => {
  for (const tabla of [
    "tableros_pictogramas",
    "frase_pictogramas"
  ]) {
    const { data, error } = await supabase
      .from(tabla)
      .select("id_pictogramas")
      .eq("id_pictogramas", id_pictograma)
      .limit(1);

    if (error) throw error;

    if (data.length > 0) return true;
  }

  return false;
};

// =====================================
// DUPLICADOS
// =====================================

const duplicadoGeneral = async (
  nombre,
  id_categorias,
  excluirId = null
) => {
  let consulta = supabase
    .from("pictogramas")
    .select("id_pictogramas, nombre")
    .eq("id_categorias", id_categorias)
    .eq("es_personalizado", false);

  if (excluirId) {
    consulta = consulta.neq("id_pictogramas", excluirId);
  }

  const { data, error } = await consulta;

  if (error) throw error;

  return data.some(
    (p) => compararNombre(p.nombre) === compararNombre(nombre)
  );
};

const duplicadoPersonalizado = async (
  id_usuario,
  nombre,
  id_categorias,
  excluirId = null
) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select(`
      id_pictogramas,
      pictogramas (
        id_pictogramas,
        id_categorias,
        nombre,
        es_personalizado
      )
    `)
    .eq("id_usuario", id_usuario);

  if (error) throw error;

  return data.some((relacion) => {
    const p = relacion.pictogramas;

    return (
      p &&
      p.es_personalizado &&
      Number(p.id_pictogramas) !== Number(excluirId) &&
      Number(p.id_categorias) === Number(id_categorias) &&
      compararNombre(p.nombre) === compararNombre(nombre)
    );
  });
};

// =====================================
// STORAGE
// =====================================

const obtenerExtension = (archivo) => {
  const extensiones = {
    "image/jpeg": "jpg",
    "image/pjpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp"
  };

  const extension = extensiones[archivo?.mimetype];

  if (!extension) {
    throw new Error("Formato de imagen no permitido");
  }

  return extension;
};

const subirImagen = async (archivo, carpeta, prefijo) => {
  const extension = obtenerExtension(archivo);

  const ruta =
    `${carpeta}/${prefijo}-${crypto.randomUUID()}.${extension}`;

  const { error } = await supabaseAdmin.storage
    .from(BUCKET)
    .upload(ruta, archivo.buffer, {
      contentType: archivo.mimetype,
      upsert: false
    });

  if (error) throw error;

  const { data } = supabaseAdmin.storage
    .from(BUCKET)
    .getPublicUrl(ruta);

  return {
    ruta,
    imagen_url: data.publicUrl
  };
};

const limpiarImagen = async (ruta) => {
  if (!ruta) return;

  const { error } = await supabaseAdmin.storage
    .from(BUCKET)
    .remove([ruta]);

  if (error) {
    console.error("Error limpiando imagen:", error.message);
  }
};

// =====================================
// GET /pictogramas
// GET /pictogramas/categoria/:id_categoria
// =====================================

const listarPictogramas = async (req, res, id_categoria = null) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const esAdmin = req.usuario?.rol === "admin";

    let consulta = supabase
      .from("pictogramas")
      .select(CAMPOS);

    if (!esAdmin) {
      consulta = consulta.eq("es_personalizado", false);
    }

    if (id_categoria !== null) {
      consulta = consulta.eq("id_categorias", id_categoria);
    }

    const { data: generales, error } = await consulta
      .order("id_pictogramas", { ascending: true });

    if (error) return manejarError(res, error);

    if (!id_usuario || esAdmin) {
      return ok(res, generales);
    }

    const { data: relaciones, error: errorRelaciones } =
      await supabase
        .from("usuarios_pictogramas")
        .select(`pictogramas (${CAMPOS})`)
        .eq("id_usuario", id_usuario);

    if (errorRelaciones) {
      return manejarError(res, errorRelaciones);
    }

    const propios = relaciones
      .map((item) => item.pictogramas)
      .filter((p) =>
        p &&
        p.es_personalizado === true &&
        (
          id_categoria === null ||
          Number(p.id_categorias) === Number(id_categoria)
        )
      );

    return ok(res, [...generales, ...propios]);

  } catch (error) {
    return manejarError(res, error);
  }
};

const obtenerPictogramas = (req, res) =>
  listarPictogramas(req, res);

const obtenerPictogramasPorCategoria = (req, res) => {
  const { id_categoria } = req.params;

  if (!idValido(id_categoria)) {
    return fallo(res, 400, "ID de categoría inválido");
  }

  return listarPictogramas(req, res, id_categoria);
};

// =====================================
// CREAR PICTOGRAMA
// =====================================

const crear = async (req, res, personalizado, conImagen) => {
  let imagenNueva = null;

  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body || {};

    if (!id_categorias || !nombre) {
      return fallo(
        res,
        400,
        "Faltan datos obligatorios: id_categorias o nombre"
      );
    }

    if (conImagen && !req.file) {
      return fallo(
        res,
        400,
        "Tenés que enviar una imagen en el campo imagen"
      );
    }

    const errorNombre = validarNombre(nombre);

    if (errorNombre) {
      return fallo(res, 400, errorNombre);
    }

    const categoria = await comprobarCategoria(
      id_categorias,
      id_usuario,
      personalizado
    );

    if (categoria.error) {
      return fallo(res, categoria.status, categoria.error);
    }

    const existe = personalizado
      ? await duplicadoPersonalizado(
          id_usuario,
          nombre,
          id_categorias
        )
      : await duplicadoGeneral(
          nombre,
          id_categorias
        );

    if (existe) {
      return fallo(
        res,
        400,
        personalizado
          ? "Ya tenés un pictograma con ese nombre en esta categoría"
          : "Ya existe un pictograma general con ese nombre en esta categoría"
      );
    }

    if (conImagen) {
      imagenNueva = await subirImagen(
        req.file,
        personalizado ? String(id_usuario) : "generales",
        personalizado ? `pictograma-${id_usuario}` : "general"
      );
    }

    const { data: pictograma, error } = await supabase
      .from("pictogramas")
      .insert([{
        id_categorias,
        nombre: normalizar(nombre),
        imagen_url: conImagen
          ? imagenNueva.imagen_url
          : (imagen_url || null),
        audio_url: audio_url || null,
        es_personalizado: personalizado
      }])
      .select(CAMPOS)
      .single();

    if (error) {
      await limpiarImagen(imagenNueva?.ruta);
      return manejarError(res, error);
    }

    if (personalizado) {
      const { error: relacionError } = await supabase
        .from("usuarios_pictogramas")
        .insert([{
          id_usuario,
          id_pictogramas: pictograma.id_pictogramas
        }]);

      if (relacionError) {
        const { error: rollbackError } = await supabase
          .from("pictogramas")
          .delete()
          .eq("id_pictogramas", pictograma.id_pictogramas);

        if (!rollbackError) {
          await limpiarImagen(imagenNueva?.ruta);
        } else {
          console.error("Falló reversión:", rollbackError.message);
        }

        return manejarError(res, relacionError);
      }

      await registrarHistorial(
        id_usuario,
        conImagen
          ? "crear_pictograma_con_imagen"
          : "crear_pictograma_personalizado",
        `Pictograma creado: ${pictograma.nombre}`
      );

    } else if (conImagen) {
      await registrarHistorial(
        id_usuario,
        "crear_pictograma_general_con_imagen",
        `Pictograma general creado: ${pictograma.nombre}`
      );
    }

    return ok(res, pictograma, 201);

  } catch (error) {
    return manejarError(res, error);
  }
};

const crearPictograma = (req, res) =>
  crear(req, res, false, false);

const crearPictogramaPersonalizado = (req, res) =>
  crear(req, res, true, false);

const crearPictogramaConImagen = (req, res) =>
  crear(req, res, false, true);

const crearPictogramaPersonalizadoConImagen = (req, res) =>
  crear(req, res, true, true);

// =====================================
// ACTUALIZAR PICTOGRAMA
// =====================================

const actualizar = async (req, res, personalizado) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(res, 400, "ID de pictograma inválido");
    }

    const pictograma = personalizado
      ? await buscarPersonalizadoPropio(id_usuario, id_pictograma)
      : await buscarPictograma(id_pictograma);

    if (!pictograma) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    if (pictograma.es_personalizado !== personalizado) {
      return fallo(res, 403, "Endpoint incorrecto para este pictograma");
    }

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body || {};

    const cambios = {};

    if (id_categorias !== undefined) {
      const categoria = await comprobarCategoria(
        id_categorias,
        id_usuario,
        personalizado
      );

      if (categoria.error) {
        return fallo(res, categoria.status, categoria.error);
      }

      cambios.id_categorias = id_categorias;
    }

    if (nombre !== undefined) {
      const errorNombre = validarNombre(nombre);

      if (errorNombre) {
        return fallo(res, 400, errorNombre);
      }

      cambios.nombre = normalizar(nombre);
    }

    if (imagen_url !== undefined) {
      cambios.imagen_url = imagen_url;
    }

    if (audio_url !== undefined) {
      cambios.audio_url = audio_url;
    }

    if (Object.keys(cambios).length === 0) {
      return fallo(res, 400, "No enviaste campos para actualizar");
    }

    if (
      personalizado &&
      await tieneOtrosUsuarios(id_pictograma, id_usuario)
    ) {
      return fallo(
        res,
        409,
        "El pictograma está compartido y no puede editarse"
      );
    }

    const nombreFinal = cambios.nombre ?? pictograma.nombre;
    const categoriaFinal =
      cambios.id_categorias ?? pictograma.id_categorias;

    const existe = personalizado
      ? await duplicadoPersonalizado(
          id_usuario,
          nombreFinal,
          categoriaFinal,
          id_pictograma
        )
      : await duplicadoGeneral(
          nombreFinal,
          categoriaFinal,
          id_pictograma
        );

    if (existe) {
      return fallo(
        res,
        400,
        "Ya existe un pictograma con ese nombre en esta categoría"
      );
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .update(cambios)
      .eq("id_pictogramas", id_pictograma)
      .eq("es_personalizado", personalizado)
      .select(CAMPOS)
      .maybeSingle();

    if (error) return manejarError(res, error);

    if (!data) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    if (personalizado) {
      await registrarHistorial(
        id_usuario,
        "actualizar_pictograma_personalizado",
        `Pictograma actualizado: ${data.nombre}`
      );
    }

    return ok(res, data);

  } catch (error) {
    return manejarError(res, error);
  }
};

const actualizarPictograma = (req, res) =>
  actualizar(req, res, false);

const actualizarPictogramaPersonalizado = (req, res) =>
  actualizar(req, res, true);

// =====================================
// ACTUALIZAR IMAGEN
// =====================================

const actualizarImagen = async (req, res, personalizado) => {
  let imagenNueva = null;

  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(res, 400, "ID de pictograma inválido");
    }

    if (!req.file) {
      return fallo(
        res,
        400,
        "Tenés que enviar una imagen en el campo imagen"
      );
    }

    const pictograma = personalizado
      ? await buscarPersonalizadoPropio(id_usuario, id_pictograma)
      : await buscarPictograma(id_pictograma);

    if (!pictograma) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    if (pictograma.es_personalizado !== personalizado) {
      return fallo(res, 403, "Endpoint incorrecto para este pictograma");
    }

    if (
      personalizado &&
      await tieneOtrosUsuarios(id_pictograma, id_usuario)
    ) {
      return fallo(
        res,
        409,
        "El pictograma está compartido y no puede editarse"
      );
    }

    imagenNueva = await subirImagen(
      req.file,
      personalizado ? String(id_usuario) : "generales",
      personalizado
        ? `pictograma-${id_usuario}-${id_pictograma}`
        : `general-${id_pictograma}`
    );

    const { data, error } = await supabase
      .from("pictogramas")
      .update({ imagen_url: imagenNueva.imagen_url })
      .eq("id_pictogramas", id_pictograma)
      .eq("es_personalizado", personalizado)
      .select(CAMPOS)
      .maybeSingle();

    if (error || !data) {
      await limpiarImagen(imagenNueva.ruta);
      return error
        ? manejarError(res, error)
        : fallo(res, 404, "Pictograma no encontrado");
    }

    await registrarHistorial(
      id_usuario,
      personalizado
        ? "actualizar_imagen_pictograma"
        : "actualizar_imagen_pictograma_general",
      `Imagen actualizada: ${data.nombre}`
    );

    return ok(res, data);

  } catch (error) {
    return manejarError(res, error);
  }
};

const actualizarImagenPictogramaPersonalizado = (req, res) =>
  actualizarImagen(req, res, true);

const actualizarImagenPictogramaGeneral = (req, res) =>
  actualizarImagen(req, res, false);

// =====================================
// GET /pictogramas/mis-personalizados
// =====================================

const obtenerMisPictogramasPersonalizados = async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario_pictograma,
        id_usuario,
        id_pictogramas,
        fecha_creacion,
        pictogramas (${CAMPOS})
      `)
      .eq("id_usuario", req.usuario.id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (error) return manejarError(res, error);

    return ok(
      res,
      data
        .map((relacion) => relacion.pictogramas)
        .filter((p) => p && p.es_personalizado)
    );

  } catch (error) {
    return manejarError(res, error);
  }
};

// =====================================
// ELIMINAR
// OPCIÓN A: BLOQUEAR SI ESTÁ EN USO
// =====================================

const eliminar = async (req, res, personalizado) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!idValido(id_pictograma)) {
      return fallo(res, 400, "ID de pictograma inválido");
    }

    const pictograma = personalizado
      ? await buscarPersonalizadoPropio(id_usuario, id_pictograma)
      : await buscarPictograma(id_pictograma);

    if (!pictograma) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    if (pictograma.es_personalizado !== personalizado) {
      return fallo(res, 403, "Endpoint incorrecto para este pictograma");
    }

    if (await estaEnUso(id_pictograma)) {
      return fallo(
        res,
        409,
        "El pictograma está utilizado en tableros o frases. Quitalo de esos lugares antes de eliminarlo."
      );
    }

    if (personalizado) {
      if (await tieneOtrosUsuarios(id_pictograma, id_usuario)) {
        return fallo(
          res,
          409,
          "El pictograma está asociado a otros usuarios"
        );
      }

      const { error: relacionError } = await supabase
        .from("usuarios_pictogramas")
        .delete()
        .eq("id_usuario", id_usuario)
        .eq("id_pictogramas", id_pictograma);

      if (relacionError) {
        return manejarError(res, relacionError);
      }
    } else {
      const { data: relaciones, error } = await supabase
        .from("usuarios_pictogramas")
        .select("id_pictogramas")
        .eq("id_pictogramas", id_pictograma)
        .limit(1);

      if (error) return manejarError(res, error);

      if (relaciones.length > 0) {
        return fallo(
          res,
          409,
          "El pictograma tiene asociaciones de usuarios activas"
        );
      }
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma)
      .eq("es_personalizado", personalizado)
      .select("id_pictogramas")
      .maybeSingle();

    if (error) {
      if (error.code === "23503") {
        return fallo(
          res,
          409,
          "El pictograma tiene relaciones activas y no puede eliminarse"
        );
      }

      return manejarError(res, error);
    }

    if (!data) {
      return fallo(res, 404, "Pictograma no encontrado");
    }

    if (personalizado) {
      await registrarHistorial(
        id_usuario,
        "eliminar_pictograma_personalizado",
        `Pictograma eliminado: ${pictograma.nombre}`
      );
    }

    return ok(res, {
      mensaje: personalizado
        ? "Pictograma personalizado eliminado correctamente"
        : "Pictograma eliminado correctamente"
    });

  } catch (error) {
    return manejarError(res, error);
  }
};

const eliminarPictograma = (req, res) =>
  eliminar(req, res, false);

const eliminarPictogramaPersonalizado = (req, res) =>
  eliminar(req, res, true);

// =====================================
// EXPORTS
// =====================================

module.exports = {
  obtenerPictogramas,
  obtenerPictogramasPorCategoria,
  crearPictograma,
  actualizarPictograma,
  eliminarPictograma,
  crearPictogramaPersonalizado,
  obtenerMisPictogramasPersonalizados,
  actualizarPictogramaPersonalizado,
  eliminarPictogramaPersonalizado,
  crearPictogramaPersonalizadoConImagen,
  actualizarImagenPictogramaPersonalizado,
  crearPictogramaConImagen,
  actualizarImagenPictogramaGeneral
};
