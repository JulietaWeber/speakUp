
const crypto = require("crypto");
const supabase = require("../config/SupabaseAdmin");

const BUCKET_CATEGORIAS = "categorias-imagenes";

const SELECT_CATEGORIA =
  "id_categorias, nombre, color, id_usuario, es_personalizada, imagen_url";

// =====================================
// HELPERS
// =====================================

const responderOk = (res, data, status = 200) =>
  res.status(status).json({ data, error: null });

const responderError = (res, status, error) =>
  res.status(status).json({ data: null, error });

const errorInterno = (res, error) => {
  console.error("Error categorías:", error);

  return responderError(
    res,
    500,
    "Ocurrió un error al procesar la categoría"
  );
};

const normalizarTexto = (valor) =>
  typeof valor === "string" ? valor.trim() : "";

const normalizarNombre = (nombre) =>
  normalizarTexto(nombre).toLowerCase();

const validarIdCategoria = (valor) => {
  if (
    valor === undefined ||
    valor === null ||
    valor === ""
  ) {
    return null;
  }

  const numero = Number(valor);

  return Number.isSafeInteger(numero) && numero > 0
    ? numero
    : null;
};

const validarNombreCategoria = (nombre) => {
  const limpio = normalizarTexto(nombre);

  if (!limpio) {
    return "El nombre de la categoría no puede estar vacío";
  }

  if (limpio.length < 2) {
    return "El nombre debe tener al menos 2 caracteres";
  }

  if (limpio.length > 40) {
    return "El nombre no puede superar los 40 caracteres";
  }

  return null;
};

const obtenerIdUsuario = (req) =>
  validarIdCategoria(req.usuario?.id_usuario);

// Consultar el usuario actual en la base.
const obtenerUsuarioActual = async (req) => {
  const id_usuario = obtenerIdUsuario(req);

  if (!id_usuario) return null;

  const { data, error } = await supabase
    .from("usuarios")
    .select("id_usuario, rol")
    .eq("id_usuario", id_usuario)
    .maybeSingle();

  if (error) throw error;

  return data;
};

const buscarCategoria = async (id_categoria) => {
  const { data, error } = await supabase
    .from("categorias")
    .select(SELECT_CATEGORIA)
    .eq("id_categorias", id_categoria)
    .maybeSingle();

  if (error) throw error;

  return data;
};

const esCategoriaGeneral = (categoria) =>
  categoria.id_usuario === null &&
  categoria.es_personalizada === false;

const esCategoriaPropia = (
  categoria,
  id_usuario
) =>
  categoria.id_usuario !== null &&
  Number(categoria.id_usuario) ===
    Number(id_usuario);

const existeCategoriaDuplicada = async ({
  id_usuario,
  nombre,
  excluirId = null
}) => {
  let consulta = supabase
    .from("categorias")
    .select("id_categorias, nombre")
    .eq("id_usuario", id_usuario);

  if (excluirId !== null) {
    consulta = consulta.neq(
      "id_categorias",
      excluirId
    );
  }

  const { data, error } = await consulta;

  if (error) throw error;

  return (data || []).some(
    (categoria) =>
      normalizarNombre(categoria.nombre) ===
      normalizarNombre(nombre)
  );
};

const registrarHistorial = async (
  id_usuario,
  accion,
  detalle
) => {
  const { error } = await supabase
    .from("historial_uso")
    .insert([{ id_usuario, accion, detalle }]);

  if (error) {
    console.error(
      "Error registrando historial:",
      error.message
    );
  }
};

// Comprobar firmas de imagen.
const validarImagen = (archivo) => {
  if (
    !archivo ||
    !Buffer.isBuffer(archivo.buffer)
  ) {
    return "Debés enviar una imagen";
  }

  if (
    archivo.size <= 0 ||
    archivo.size > 2 * 1024 * 1024
  ) {
    return "La imagen debe tener un máximo de 2 MB";
  }

  const buffer = archivo.buffer;
  const tipo = archivo.mimetype;

  const png =
    tipo === "image/png" &&
    buffer.length >= 8 &&
    buffer.subarray(0, 8).equals(
      Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])
    );

  const jpg =
    tipo === "image/jpeg" &&
    buffer.length >= 3 &&
    buffer[0] === 0xff &&
    buffer[1] === 0xd8 &&
    buffer[2] === 0xff;

  const webp =
    tipo === "image/webp" &&
    buffer.length >= 12 &&
    buffer.toString("ascii", 0, 4) === "RIFF" &&
    buffer.toString("ascii", 8, 12) === "WEBP";

  if (!png && !jpg && !webp) {
    return "Solo se permiten imágenes PNG, JPG o WEBP válidas";
  }

  return null;
};

// =====================================
// GET /categorias
// Categorías generales públicas
// =====================================

const obtenerCategorias = async (req, res) => {
  try {
    const { data, error } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .is("id_usuario", null)
      .eq("es_personalizada", false)
      .order("id_categorias", {
        ascending: true
      });

    if (error) return errorInterno(res, error);

    return responderOk(res, data || []);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// GET /categorias/mis-categorias
// Generales + personalizadas propias
// =====================================

const obtenerMisCategorias = async (req, res) => {
  try {
    const usuario = await obtenerUsuarioActual(req);

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    const { data, error } = await supabase
      .from("categorias")
      .select(SELECT_CATEGORIA)
      .or(
        `id_usuario.is.null,id_usuario.eq.${usuario.id_usuario}`
      )
      .order("id_categorias", {
        ascending: true
      });

    if (error) return errorInterno(res, error);

    // Defensa adicional ante categorías mal configuradas.
    const visibles = (data || []).filter(
      (categoria) =>
        esCategoriaGeneral(categoria) ||
        esCategoriaPropia(
          categoria,
          usuario.id_usuario
        )
    );

    return responderOk(res, visibles);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// GET /categorias/:id_categoria
// =====================================

const obtenerCategoriaPorId = async (req, res) => {
  try {
    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(
        res,
        400,
        "ID de categoría inválido"
      );
    }

    const categoria = await buscarCategoria(
      id_categoria
    );

    if (!categoria) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    // Esta ruta no tiene autenticación obligatoria.
    // Solo se muestran categorías generales.
    if (!esCategoriaGeneral(categoria)) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    return responderOk(res, categoria);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// POST /categorias
// =====================================

const crearCategoria = async (req, res) => {
  try {
    const usuario = await obtenerUsuarioActual(req);

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    const { nombre, color } = req.body || {};

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombreCategoria(
      nombreLimpio
    );

    if (errorNombre) {
      return responderError(
        res,
        400,
        errorNombre
      );
    }

    const duplicada = await existeCategoriaDuplicada({
      id_usuario: usuario.id_usuario,
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
          id_usuario: usuario.id_usuario,
          es_personalizada: true,
          imagen_url: null
        }
      ])
      .select(SELECT_CATEGORIA)
      .single();

    if (error) return errorInterno(res, error);

    await registrarHistorial(
      usuario.id_usuario,
      "crear_categoria",
      `Categoría creada: ${nombreLimpio}`
    );

    return responderOk(res, data, 201);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// PUT /categorias/:id_categoria
// =====================================

const actualizarCategoria = async (req, res) => {
  try {
    const usuario = await obtenerUsuarioActual(req);

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(
        res,
        400,
        "ID de categoría inválido"
      );
    }

    const categoria = await buscarCategoria(
      id_categoria
    );

    if (!categoria) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    if (esCategoriaGeneral(categoria)) {
      return responderError(
        res,
        403,
        "No se puede modificar una categoría default del sistema"
      );
    }

    if (
      !categoria.es_personalizada ||
      !esCategoriaPropia(
        categoria,
        usuario.id_usuario
      )
    ) {
      return responderError(
        res,
        403,
        "No tenés permiso para modificar esta categoría"
      );
    }

    const { nombre, color } = req.body || {};
    const cambios = {};

    if (nombre !== undefined) {
      const nombreLimpio = normalizarTexto(nombre);
      const errorNombre = validarNombreCategoria(
        nombreLimpio
      );

      if (errorNombre) {
        return responderError(
          res,
          400,
          errorNombre
        );
      }

      const duplicada =
        await existeCategoriaDuplicada({
          id_usuario: usuario.id_usuario,
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

      cambios.nombre = nombreLimpio;
    }

    if (color !== undefined) {
      cambios.color = color;
    }

    if (Object.keys(cambios).length === 0) {
      return responderError(
        res,
        400,
        "No enviaste campos para actualizar"
      );
    }

    const { data, error } = await supabase
      .from("categorias")
      .update(cambios)
      .eq("id_categorias", id_categoria)
      .eq("id_usuario", usuario.id_usuario)
      .eq("es_personalizada", true)
      .select(SELECT_CATEGORIA)
      .maybeSingle();

    if (error) return errorInterno(res, error);

    if (!data) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    await registrarHistorial(
      usuario.id_usuario,
      "actualizar_categoria",
      `Categoría actualizada: ${data.nombre}`
    );

    return responderOk(res, data);

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// PUT /categorias/:id_categoria/imagen
// =====================================

const actualizarImagenCategoria = async (req, res) => {
  let rutaArchivo = null;

  try {
    const usuario = await obtenerUsuarioActual(req);

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(
        res,
        400,
        "ID de categoría inválido"
      );
    }

    const errorImagen = validarImagen(req.file);

    if (errorImagen) {
      return responderError(
        res,
        400,
        errorImagen
      );
    }

    const categoria = await buscarCategoria(
      id_categoria
    );

    if (!categoria) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    const esGeneral = esCategoriaGeneral(categoria);

    const esPropia =
      categoria.es_personalizada === true &&
      esCategoriaPropia(
        categoria,
        usuario.id_usuario
      );

    const esAdmin = usuario.rol === "admin";

    // Admin puede cambiar imágenes generales.
    // Usuario puede cambiar las de sus categorías.
    if (
      !(esGeneral && esAdmin) &&
      !esPropia
    ) {
      return responderError(
        res,
        403,
        "No tenés permiso para modificar esta imagen"
      );
    }

    const extensionPorTipo = {
      "image/png": "png",
      "image/jpeg": "jpg",
      "image/webp": "webp"
    };

    const extension =
      extensionPorTipo[req.file.mimetype];

    rutaArchivo =
      `categorias/${id_categoria}/` +
      `${crypto.randomUUID()}.${extension}`;

    const { error: subirError } =
      await supabase.storage
        .from(BUCKET_CATEGORIAS)
        .upload(
          rutaArchivo,
          req.file.buffer,
          {
            contentType: req.file.mimetype,
            upsert: false
          }
        );

    if (subirError) {
      return errorInterno(res, subirError);
    }

    const { data: urlData } =
      supabase.storage
        .from(BUCKET_CATEGORIAS)
        .getPublicUrl(rutaArchivo);

    const imagen_url = urlData.publicUrl;

    const { data, error } = await supabase
      .from("categorias")
      .update({ imagen_url })
      .eq("id_categorias", id_categoria)
      .select(SELECT_CATEGORIA)
      .maybeSingle();

    if (error || !data) {
      await supabase.storage
        .from(BUCKET_CATEGORIAS)
        .remove([rutaArchivo]);

      return error
        ? errorInterno(res, error)
        : responderError(
            res,
            404,
            "Categoría no encontrada"
          );
    }

    await registrarHistorial(
      usuario.id_usuario,
      "actualizar_imagen_categoria",
      `Imagen actualizada: ${data.nombre}`
    );

    return responderOk(res, data);

  } catch (error) {
    if (rutaArchivo) {
      await supabase.storage
        .from(BUCKET_CATEGORIAS)
        .remove([rutaArchivo]);
    }

    return errorInterno(res, error);
  }
};

// =====================================
// DELETE /categorias/:id_categoria
// =====================================

const eliminarCategoria = async (req, res) => {
  try {
    const usuario = await obtenerUsuarioActual(req);

    if (!usuario) {
      return responderError(
        res,
        401,
        "Usuario no encontrado o sesión inválida"
      );
    }

    const id_categoria = validarIdCategoria(
      req.params.id_categoria
    );

    if (!id_categoria) {
      return responderError(
        res,
        400,
        "ID de categoría inválido"
      );
    }

    const categoria = await buscarCategoria(
      id_categoria
    );

    if (!categoria) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    if (esCategoriaGeneral(categoria)) {
      return responderError(
        res,
        403,
        "No se puede eliminar una categoría default del sistema"
      );
    }

    if (
      !categoria.es_personalizada ||
      !esCategoriaPropia(
        categoria,
        usuario.id_usuario
      )
    ) {
      return responderError(
        res,
        403,
        "No tenés permiso para eliminar esta categoría"
      );
    }

    const {
      data: pictogramasCategoria,
      error: pictogramasError
    } = await supabase
      .from("pictogramas")
      .select("id_pictogramas")
      .eq("id_categorias", id_categoria);

    if (pictogramasError) {
      return errorInterno(res, pictogramasError);
    }

    const idsPictogramas =
      (pictogramasCategoria || []).map(
        (p) => p.id_pictogramas
      );

    if (idsPictogramas.length > 0) {
      // No eliminar pictogramas que tengan relaciones.
      const tablasRelacionadas = [
        "frase_pictogramas",
        "tableros_pictogramas",
        "usuarios_pictogramas"
      ];

      for (const tabla of tablasRelacionadas) {
        const { count, error } = await supabase
          .from(tabla)
          .select("*", {
            count: "exact",
            head: true
          })
          .in("id_pictogramas", idsPictogramas);

        if (error) {
          return errorInterno(res, error);
        }

        if (count > 0) {
          return responderError(
            res,
            409,
            "No se puede eliminar la categoría porque contiene pictogramas en uso"
          );
        }
      }

      const { error } = await supabase
        .from("pictogramas")
        .delete()
        .in("id_pictogramas", idsPictogramas);

      if (error) {
        return errorInterno(res, error);
      }
    }

    const { data: eliminada, error } =
      await supabase
        .from("categorias")
        .delete()
        .eq("id_categorias", id_categoria)
        .eq("id_usuario", usuario.id_usuario)
        .eq("es_personalizada", true)
        .select("id_categorias")
        .maybeSingle();

    if (error) return errorInterno(res, error);

    if (!eliminada) {
      return responderError(
        res,
        404,
        "Categoría no encontrada"
      );
    }

    await registrarHistorial(
      usuario.id_usuario,
      "eliminar_categoria",
      `Categoría eliminada: ${categoria.nombre}`
    );

    return responderOk(res, {
      mensaje: "Categoría eliminada correctamente",
      pictogramas_eliminados:
        idsPictogramas.length
    });

  } catch (error) {
    return errorInterno(res, error);
  }
};

// =====================================
// EXPORTACIONES
// =====================================

module.exports = {
  obtenerCategorias,
  obtenerMisCategorias,
  obtenerCategoriaPorId,
  crearCategoria,
  actualizarCategoria,
  actualizarImagenCategoria,
  eliminarCategoria
};
