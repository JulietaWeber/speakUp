const supabaseAdmin = require("../config/SupabaseAdmin");
const crypto = require("crypto");

const SELECT_CATEGORIA =
  "id_categorias, nombre, color, id_usuario, es_personalizada, imagen_url";

const responderError = (res, status, error) => {
  return res.status(status).json({
    data: null,
    error
  });
};

const normalizarTexto = (texto) => {
  return String(texto || "").trim();
};

const normalizarNombre = (nombre) => {
  return normalizarTexto(nombre).toLowerCase();
};

const validarNombreCategoria = (nombre) => {
  const nombreLimpio = normalizarTexto(nombre);

  if (!nombreLimpio) {
    return "El nombre de la categoría no puede estar vacío";
  }

  if (nombreLimpio.length < 2) {
    return "El nombre de la categoría debe tener al menos 2 caracteres";
  }

  if (nombreLimpio.length > 40) {
    return "El nombre de la categoría no puede superar los 40 caracteres";
  }

  return null;
};

const existeCategoriaDuplicada = async ({
  id_usuario,
  nombre,
  excluirId = null
}) => {
  let query = supabase
    .from("categorias")
    .select("id_categorias, nombre")
    .eq("id_usuario", id_usuario);

  if (excluirId) {
    query = query.neq("id_categorias", excluirId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(error.message);
  }

  const nombreComparar = normalizarNombre(nombre);

  return data.some((categoria) => {
    return normalizarNombre(categoria.nombre) === nombreComparar;
  });
};

// GET /categorias
const obtenerCategorias = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;

    let query = supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .order("id_categorias", { ascending: true });

    if (id_usuario) {
      query = query.or(`id_usuario.is.null,id_usuario.eq.${id_usuario}`);
    } else {
      query = query.is("id_usuario", null);
    }

    const { data, error } = await query;

    if (error) {
      return responderError(res, 500, error.message);
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /categorias/mis-categorias
const obtenerMisCategorias = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .or(`id_usuario.is.null,id_usuario.eq.${id_usuario}`)
      .order("id_categorias", { ascending: true });

    if (error) {
      return responderError(res, 500, error.message);
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /categorias/:id_categoria
const obtenerCategoriaPorId = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const { id_categoria } = req.params;

    const { data: categoria, error } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .eq("id_categorias", id_categoria)
      .maybeSingle();

    if (error) {
      return responderError(res, 500, error.message);
    }

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    const esGeneral = categoria.id_usuario === null;
    const esPropia = Number(categoria.id_usuario) === Number(id_usuario);

    if (!esGeneral && !esPropia) {
      return responderError(res, 403, "No tenés permiso para ver esta categoría");
    }

    return res.json({
      data: categoria,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// POST /categorias
const crearCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { nombre, color } = req.body;

    if (!nombre) {
      return responderError(res, 400, "Falta el nombre de la categoría");
    }

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombreCategoria(nombreLimpio);

    if (errorNombre) {
      return responderError(res, 400, errorNombre);
    }

    const duplicada = await existeCategoriaDuplicada({
      id_usuario,
      nombre: nombreLimpio
    });

    if (duplicada) {
      return responderError(res, 400, "Ya tenés una categoría con ese nombre");
    }

    const { data, error } = await supabase
      .from("categorias")
      .insert([
        {
          nombre: nombreLimpio,
          color: color || null,
          id_usuario,
          es_personalizada: true
        }
      ])
      .select(SELECT_CATEGORIA)
      .single();

    if (error) {
      return responderError(res, 500, error.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_categoria",
        detalle: `Categoría creada: ${nombreLimpio}`
      }
    ]);

    return res.status(201).json({
      data,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// PUT /categorias/:id_categoria
const actualizarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_categoria } = req.params;
    const { nombre, color } = req.body;

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .eq("id_categorias", id_categoria)
      .maybeSingle();

    if (categoriaError) {
      return responderError(res, 500, categoriaError.message);
    }

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    if (categoria.id_usuario === null || categoria.es_personalizada === false) {
      return responderError(res, 403, "No se puede modificar una categoría default del sistema");
    }

    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return responderError(res, 403, "No tenés permiso para modificar esta categoría");
    }

    const camposActualizar = {};

    if (nombre !== undefined) {
      const nombreLimpio = normalizarTexto(nombre);
      const errorNombre = validarNombreCategoria(nombreLimpio);

      if (errorNombre) {
        return responderError(res, 400, errorNombre);
      }

      const duplicada = await existeCategoriaDuplicada({
        id_usuario,
        nombre: nombreLimpio,
        excluirId: id_categoria
      });

      if (duplicada) {
        return responderError(res, 400, "Ya tenés una categoría con ese nombre");
      }

      camposActualizar.nombre = nombreLimpio;
    }

    if (color !== undefined) {
      camposActualizar.color = color;
    }

    if (Object.keys(camposActualizar).length === 0) {
      return responderError(res, 400, "No enviaste campos para actualizar");
    }

    const { data, error } = await supabase
      .from("categorias")
      .update(camposActualizar)
      .eq("id_categorias", id_categoria)
      .select(SELECT_CATEGORIA)
      .single();

    if (error) {
      return responderError(res, 500, error.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "actualizar_categoria",
        detalle: `Categoría actualizada: ${data.nombre}`
      }
    ]);

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// DELETE /categorias/:id_categoria
const eliminarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_categoria } = req.params;

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .eq("id_categorias", id_categoria)
      .maybeSingle();

    if (categoriaError) {
      return responderError(res, 500, categoriaError.message);
    }

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    if (categoria.id_usuario === null || categoria.es_personalizada === false) {
      return responderError(res, 403, "No se puede eliminar una categoría default del sistema");
    }

    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return responderError(res, 403, "No tenés permiso para eliminar esta categoría");
    }

    const { data: pictogramasCategoria, error: pictogramasError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas")
      .eq("id_categorias", id_categoria);

    if (pictogramasError) {
      return responderError(res, 500, pictogramasError.message);
    }

    const idsPictogramas = pictogramasCategoria.map((p) => p.id_pictogramas);

    if (idsPictogramas.length > 0) {
      await supabase
        .from("tableros_pictogramas")
        .delete()
        .in("id_pictogramas", idsPictogramas);

      await supabase
        .from("usuarios_pictogramas")
        .delete()
        .in("id_pictogramas", idsPictogramas);

      await supabase
        .from("frase_pictogramas")
        .delete()
        .in("id_pictogramas", idsPictogramas);

      const { error: borrarPictogramasError } = await supabase
        .from("pictogramas")
        .delete()
        .in("id_pictogramas", idsPictogramas);

      if (borrarPictogramasError) {
        return responderError(res, 500, borrarPictogramasError.message);
      }
    }

    const { error } = await supabase
      .from("categorias")
      .delete()
      .eq("id_categorias", id_categoria);

    if (error) {
      return responderError(res, 500, error.message);
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "eliminar_categoria",
        detalle: `Categoría eliminada: ${categoria.nombre}`
      }
    ]);

    return res.json({
      data: {
        mensaje: "Categoría eliminada correctamente",
        pictogramas_eliminados: idsPictogramas.length
      },
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};


const actualizarImagenCategoria = async (req, res) => {
  try {
    const idCategoria = Number(req.params.id_categoria);
    const idUsuario = Number(req.usuario.id_usuario);

    if (!Number.isSafeInteger(idCategoria) || idCategoria <= 0) {
      return responderError(res, 400, "ID de categoría inválido");
    }

    if (!req.file) {
      return responderError(res, 400, "Debés enviar una imagen");
    }

    const formatos = {
      "image/png": "png",
      "image/jpeg": "jpg",
      "image/webp": "webp"
    };

    const extension = formatos[req.file.mimetype];

    if (!extension || req.file.size > 2 * 1024 * 1024) {
      return responderError(res, 400, "Imagen inválida o mayor a 2 MB");
    }

    const buffer = req.file.buffer;
    const esImagenReal =
      (extension === "png" &&
        buffer.subarray(0, 8).equals(
          Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
        )) ||
      (extension === "jpg" &&
        buffer[0] === 0xff &&
        buffer[1] === 0xd8 &&
        buffer[2] === 0xff) ||
      (extension === "webp" &&
        buffer.toString("ascii", 0, 4) === "RIFF" &&
        buffer.toString("ascii", 8, 12) === "WEBP");

    if (!esImagenReal) {
      return responderError(res, 400, "El archivo no es una imagen válida");
    }

    const { data: categoria, error: buscarError } =
      await supabaseAdmin
        .from("categorias")
        .select("id_categorias, id_usuario, es_personalizada")
        .eq("id_categorias", idCategoria)
        .maybeSingle();

    if (buscarError) throw buscarError;

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    const esAdmin = req.usuario.rol === "admin";
    const esPropia =
      categoria.id_usuario !== null &&
      Number(categoria.id_usuario) === idUsuario;

    const esGeneral =
      categoria.id_usuario === null &&
      categoria.es_personalizada === false;

    if (
      (esGeneral && !esAdmin) ||
      (!esGeneral && !esPropia && !esAdmin)
    ) {
      return responderError(res, 403, "No tenés permiso para modificar esta categoría");
    }

    const ruta = `categorias/${idCategoria}/${crypto.randomUUID()}.${extension}`;

    const { error: subirError } = await supabaseAdmin.storage
      .from("categorias-imagenes")
      .upload(ruta, buffer, {
        contentType: req.file.mimetype,
        upsert: false
      });

    if (subirError) throw subirError;

    const { data: urlData } = supabaseAdmin.storage
      .from("categorias-imagenes")
      .getPublicUrl(ruta);

    const { data, error: actualizarError } = await supabaseAdmin
      .from("categorias")
      .update({ imagen_url: urlData.publicUrl })
      .eq("id_categorias", idCategoria)
      .select(SELECT_CATEGORIA)
      .single();

    if (actualizarError) {
      await supabaseAdmin.storage
        .from("categorias-imagenes")
        .remove([ruta]);

      throw actualizarError;
    }

    return res.json({ data, error: null });

  } catch (error) {
    console.error("Error al actualizar imagen:", error);
    return responderError(res, 500, "No se pudo actualizar la imagen");
  }
};


module.exports = {
  obtenerCategorias,
  obtenerCategoriaPorId,
  obtenerMisCategorias,
  crearCategoria,
  actualizarCategoria,
  eliminarCategoria,
  actualizarImagenCategoria
};