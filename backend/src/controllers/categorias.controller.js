
const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");
const crypto = require("crypto");

const BUCKET_CATEGORIAS = "categorias-imagenes";

const SELECT_CATEGORIA =
  "id_categorias, nombre, color, id_usuario, es_personalizada, imagen_url";

// ======================================
// HELPERS
// ======================================

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

  if (excluirId !== null) {
    query = query.neq("id_categorias", excluirId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(error.message);
  }

  const nombreComparar = normalizarNombre(nombre);

  return (data || []).some((categoria) => {
    return normalizarNombre(categoria.nombre) === nombreComparar;
  });
};

const validarIdCategoria = (valor) => {
  const id = Number(valor);
  return Number.isSafeInteger(id) && id > 0 ? id : null;
};

const validarImagen = (archivo) => {
  if (!archivo || !archivo.buffer) {
    return "Debés enviar una imagen";
  }

  if (archivo.size > 2 * 1024 * 1024) {
    return "La imagen supera los 2 MB";
  }

  const buffer = archivo.buffer;
  const tipo = archivo.mimetype;

  if (tipo === "image/png") {
    const firmaPNG = Buffer.from([
      137, 80, 78, 71, 13, 10, 26, 10
    ]);

    if (buffer.length >= 8 &&
        buffer.subarray(0, 8).equals(firmaPNG)) {
      return null;
    }
  }

  if (tipo === "image/jpeg") {
    if (
      buffer.length >= 3 &&
      buffer[0] === 0xff &&
      buffer[1] === 0xd8 &&
      buffer[2] === 0xff
    ) {
      return null;
    }
  }

  if (tipo === "image/webp") {
    if (
      buffer.length >= 12 &&
      buffer.toString("ascii", 0, 4) === "RIFF" &&
      buffer.toString("ascii", 8, 12) === "WEBP"
    ) {
      return null;
    }
  }

  return "Solo se permiten imágenes PNG, JPG o WEBP válidas";
};

// ======================================
// GET /categorias
// ======================================

const obtenerCategorias = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;

    let query = supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .order("id_categorias", { ascending: true });

    if (id_usuario) {
      query = query.or(
        `id_usuario.is.null,id_usuario.eq.${id_usuario}`
      );
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

// ======================================
// GET /categorias/mis-categorias
// ======================================

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

// ======================================
// GET /categorias/:id_categoria
// ======================================

const obtenerCategoriaPorId = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(res, 400, "ID de categoría inválido");
    }

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

    const esPropia =
      id_usuario !== null &&
      Number(categoria.id_usuario) === Number(id_usuario);

    if (!esGeneral && !esPropia) {
      return responderError(
        res,
        403,
        "No tenés permiso para ver esta categoría"
      );
    }

    return res.json({
      data: categoria,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// ======================================
// POST /categorias
// ======================================

const crearCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { nombre, color } = req.body;

    if (!nombre) {
      return responderError(
        res,
        400,
        "Falta el nombre de la categoría"
      );
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
      return responderError(
        res,
        400,
        "Ya tenés una categoría con ese nombre"
      );
    }

    const { data, error } = await supabase
      .from("categorias")
      .insert([
        {
          nombre: nombreLimpio,
          color: color || null,
          id_usuario,
          es_personalizada: true,
          imagen_url: null
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

// ======================================
// PUT /categorias/:id_categoria
// ======================================

const actualizarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );
    const { nombre, color } = req.body;

    if (!id_categoria) {
      return responderError(res, 400, "ID de categoría inválido");
    }

    const { data: categoria, error: categoriaError } =
      await supabase
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

    if (
      categoria.id_usuario === null ||
      categoria.es_personalizada === false
    ) {
      return responderError(
        res,
        403,
        "No se puede modificar una categoría default del sistema"
      );
    }

    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return responderError(
        res,
        403,
        "No tenés permiso para modificar esta categoría"
      );
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
        return responderError(
          res,
          400,
          "Ya tenés una categoría con ese nombre"
        );
      }

      camposActualizar.nombre = nombreLimpio;
    }

    if (color !== undefined) {
      camposActualizar.color = color;
    }

    if (Object.keys(camposActualizar).length === 0) {
      return responderError(
        res,
        400,
        "No enviaste campos para actualizar"
      );
    }

    const { data, error } = await supabase
      .from("categorias")
      .update(camposActualizar)
      .eq("id_categorias", id_categoria)
      .eq("id_usuario", id_usuario)
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

// ======================================
// PUT /categorias/:id_categoria/imagen
// ======================================

const actualizarImagenCategoria = async (req, res) => {
  let rutaArchivo = null;

  try {
    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    const id_usuario = req.usuario.id_usuario;

    if (!id_categoria) {
      return responderError(res, 400, "ID de categoría inválido");
    }

    const errorImagen = validarImagen(req.file);

    if (errorImagen) {
      return responderError(res, 400, errorImagen);
    }

    // Consultar categoría
    const { data: categoria, error: buscarError } =
      await supabaseAdmin
        .from("categorias")
        .select(
          "id_categorias, id_usuario, es_personalizada"
        )
        .eq("id_categorias", id_categoria)
        .maybeSingle();

    if (buscarError) {
      return responderError(res, 500, buscarError.message);
    }

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    // Validar permisos
    const esAdmin = req.usuario.rol === "admin";

    const esPropia =
      categoria.id_usuario !== null &&
      Number(categoria.id_usuario) === Number(id_usuario);

    const esGeneral =
      categoria.id_usuario === null &&
      categoria.es_personalizada === false;

    if (esGeneral && !esAdmin) {
      return responderError(
        res,
        403,
        "Solo un administrador puede cambiar imágenes generales"
      );
    }

    if (!esGeneral && !esPropia && !esAdmin) {
      return responderError(
        res,
        403,
        "No tenés permiso para modificar esta categoría"
      );
    }

    // Determinar extensión
    const extensiones = {
      "image/png": "png",
      "image/jpeg": "jpg",
      "image/webp": "webp"
    };

    const extension = extensiones[req.file.mimetype];

    rutaArchivo =
      `categorias/${id_categoria}/${crypto.randomUUID()}.${extension}`;

    // Subir imagen a Supabase Storage
    const { error: subirError } = await supabaseAdmin.storage
      .from(BUCKET_CATEGORIAS)
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: false
      });

    if (subirError) {
      return responderError(res, 500, subirError.message);
    }

    // Obtener URL pública
    const { data: urlData } = supabaseAdmin.storage
      .from(BUCKET_CATEGORIAS)
      .getPublicUrl(rutaArchivo);

    const imagen_url = urlData.publicUrl;

    // Guardar la URL en la categoría
    const { data, error: actualizarError } =
      await supabaseAdmin
        .from("categorias")
        .update({ imagen_url })
        .eq("id_categorias", id_categoria)
        .select(SELECT_CATEGORIA)
        .single();

    if (actualizarError) {
      await supabaseAdmin.storage
        .from(BUCKET_CATEGORIAS)
        .remove([rutaArchivo]);

      return responderError(
        res,
        500,
        actualizarError.message
      );
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    console.error("Error imagen categoría:", error);

    return responderError(
      res,
      500,
      "No se pudo actualizar la imagen de la categoría"
    );
  }
};

// ======================================
// DELETE /categorias/:id_categoria
// ======================================

const eliminarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(res, 400, "ID de categoría inválido");
    }

    const { data: categoria, error: categoriaError } =
      await supabase
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

    if (
      categoria.id_usuario === null ||
      categoria.es_personalizada === false
    ) {
      return responderError(
        res,
        403,
        "No se puede eliminar una categoría default del sistema"
      );
    }

    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return responderError(
        res,
        403,
        "No tenés permiso para eliminar esta categoría"
      );
    }

    const { data: pictogramasCategoria, error: pictogramasError } =
      await supabase
        .from("pictogramas")
        .select("id_pictogramas")
        .eq("id_categorias", id_categoria);

    if (pictogramasError) {
      return responderError(res, 500, pictogramasError.message);
    }

    const idsPictogramas =
      (pictogramasCategoria || []).map(
        (p) => p.id_pictogramas
      );

    // Evitar eliminar pictogramas que se estén utilizando
    if (idsPictogramas.length > 0) {
      const tablasRelacionadas = [
        "frase_pictogramas",
        "tableros_pictogramas",
        "usuarios_pictogramas"
      ];

      for (const tabla of tablasRelacionadas) {
        const { count, error } = await supabase
          .from(tabla)
          .select("*", { count: "exact", head: true })
          .in("id_pictogramas", idsPictogramas);

        if (error) {
          return responderError(res, 500, error.message);
        }

        if (count > 0) {
          return responderError(
            res,
            409,
            "No se puede eliminar la categoría porque contiene pictogramas en uso"
          );
        }
      }

      const { error: borrarPictogramasError } =
        await supabase
          .from("pictogramas")
          .delete()
          .in("id_pictogramas", idsPictogramas);

      if (borrarPictogramasError) {
        return responderError(
          res,
          500,
          borrarPictogramasError.message
        );
      }
    }

    const { error } = await supabase
      .from("categorias")
      .delete()
      .eq("id_categorias", id_categoria)
      .eq("id_usuario", id_usuario);

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

// ======================================
// EXPORTACIONES
// ======================================

module.exports = {
  obtenerCategorias,
  obtenerCategoriaPorId,
  obtenerMisCategorias,
  crearCategoria,
  actualizarCategoria,
  actualizarImagenCategoria,
  eliminarCategoria
};
