const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");

const SELECT_PICTOGRAMA =
  "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado";

const responderError = (res, status, error) => {
  return res.status(status).json({
    data: null,
    error
  });
};

const normalizarTexto = (texto) => {
  return String(texto || "").trim();
};

const normalizarNombreParaComparar = (nombre) => {
  return normalizarTexto(nombre).toLowerCase();
};

const validarNombrePictograma = (nombre) => {
  const nombreLimpio = normalizarTexto(nombre);

  if (!nombreLimpio) {
    return "El nombre del pictograma no puede estar vacío";
  }

  if (nombreLimpio.length < 2) {
    return "El nombre del pictograma debe tener al menos 2 caracteres";
  }

  if (nombreLimpio.length > 50) {
    return "El nombre del pictograma no puede superar los 50 caracteres";
  }

  const palabrasBloqueadas = [
    "poronga",
    "pete"
  ];

  if (palabrasBloqueadas.includes(nombreLimpio.toLowerCase())) {
    return "El nombre del pictograma no está permitido";
  }

  return null;
};

const normalizarExtensionImagen = (nombreOriginal) => {
  let extension = nombreOriginal
    .split(".")
    .pop()
    .toLowerCase();

  if (extension === "jfif" || extension === "jpeg") {
    extension = "jpg";
  }

  return extension;
};

const subirImagenPictograma = async ({ archivo, carpeta, nombreBase }) => {
  const extension = normalizarExtensionImagen(archivo.originalname);
  const nombreArchivo = `${nombreBase}-${Date.now()}.${extension}`;
  const rutaArchivo = `${carpeta}/${nombreArchivo}`;

  const { error: uploadError } = await supabaseAdmin.storage
    .from("pictogramas-imagenes")
    .upload(rutaArchivo, archivo.buffer, {
      contentType: archivo.mimetype,
      upsert: true
    });

  if (uploadError) {
    throw new Error(uploadError.message);
  }

  const { data: publicUrlData } = supabaseAdmin.storage
    .from("pictogramas-imagenes")
    .getPublicUrl(rutaArchivo);

  return publicUrlData.publicUrl;
};

const registrarHistorial = async ({ id_usuario, accion, detalle }) => {
  await supabase.from("historial_uso").insert([
    {
      id_usuario,
      accion,
      detalle
    }
  ]);
};

const obtenerCategoria = async (id_categorias) => {
  const { data, error } = await supabase
    .from("categorias")
    .select("id_categorias, nombre, id_usuario, es_personalizada")
    .eq("id_categorias", id_categorias)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
};

const usuarioPuedeUsarCategoria = (categoria, id_usuario) => {
  const categoriaEsDefault =
    categoria.id_usuario === null || categoria.es_personalizada === false;

  const categoriaEsPropia =
    Number(categoria.id_usuario) === Number(id_usuario);

  return categoriaEsDefault || categoriaEsPropia;
};

const verificarPictogramaPropio = async (id_usuario, id_pictograma) => {
  const { data, error } = await supabase
    .from("usuarios_pictogramas")
    .select(`
      id_usuario,
      id_pictogramas,
      pictogramas (
        id_pictogramas,
        id_categorias,
        nombre,
        imagen_url,
        audio_url,
        es_personalizado
      )
    `)
    .eq("id_usuario", id_usuario)
    .eq("id_pictogramas", id_pictograma)
    .maybeSingle();

  if (error) {
    throw new Error(error.message);
  }

  return data;
};

const existePictogramaGeneralDuplicado = async ({
  nombre,
  id_categorias,
  excluirId = null
}) => {
  let query = supabase
    .from("pictogramas")
    .select("id_pictogramas, nombre")
    .eq("id_categorias", id_categorias)
    .eq("es_personalizado", false);

  if (excluirId) {
    query = query.neq("id_pictogramas", excluirId);
  }

  const { data, error } = await query;

  if (error) {
    throw new Error(error.message);
  }

  const nombreComparar = normalizarNombreParaComparar(nombre);

  return data.some((pictograma) => {
    return normalizarNombreParaComparar(pictograma.nombre) === nombreComparar;
  });
};

const existePictogramaPersonalizadoDuplicado = async ({
  id_usuario,
  nombre,
  id_categorias,
  excluirId = null
}) => {
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

  if (error) {
    throw new Error(error.message);
  }

  const nombreComparar = normalizarNombreParaComparar(nombre);

  return data.some((item) => {
    const pictograma = item.pictogramas;

    if (!pictograma) return false;

    if (excluirId && Number(pictograma.id_pictogramas) === Number(excluirId)) {
      return false;
    }

    return (
      Number(pictograma.id_categorias) === Number(id_categorias) &&
      pictograma.es_personalizado === true &&
      normalizarNombreParaComparar(pictograma.nombre) === nombreComparar
    );
  });
};

// GET /pictogramas
const obtenerPictogramas = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const rol = req.usuario?.rol || null;

    if (rol === "admin") {
      const { data, error } = await supabase
        .from("pictogramas")
        .select(SELECT_PICTOGRAMA)
        .order("id_pictogramas", { ascending: true });

      if (error) {
        return responderError(res, 500, error.message);
      }

      return res.json({
        data,
        error: null
      });
    }

    const { data: pictogramasGenerales, error: generalesError } = await supabase
      .from("pictogramas")
      .select(SELECT_PICTOGRAMA)
      .eq("es_personalizado", false)
      .order("id_pictogramas", { ascending: true });

    if (generalesError) {
      return responderError(res, 500, generalesError.message);
    }

    if (!id_usuario) {
      return res.json({
        data: pictogramasGenerales,
        error: null
      });
    }

    const { data: relaciones, error: relacionesError } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario,
        id_pictogramas,
        pictogramas (
          id_pictogramas,
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        )
      `)
      .eq("id_usuario", id_usuario);

    if (relacionesError) {
      return responderError(res, 500, relacionesError.message);
    }

    const pictogramasPropios = relaciones
      .map((item) => item.pictogramas)
      .filter(Boolean)
      .filter((pictograma) => pictograma.es_personalizado === true);

    return res.json({
      data: [
        ...pictogramasGenerales,
        ...pictogramasPropios
      ],
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /pictogramas/categoria/:id_categoria
const obtenerPictogramasPorCategoria = async (req, res) => {
  try {
    const { id_categoria } = req.params;
    const id_usuario = req.usuario?.id_usuario || null;
    const rol = req.usuario?.rol || null;

    if (rol === "admin") {
      const { data, error } = await supabase
        .from("pictogramas")
        .select(SELECT_PICTOGRAMA)
        .eq("id_categorias", id_categoria)
        .order("id_pictogramas", { ascending: true });

      if (error) {
        return responderError(res, 500, error.message);
      }

      return res.json({
        data,
        error: null
      });
    }

    const { data: pictogramasGenerales, error: generalesError } = await supabase
      .from("pictogramas")
      .select(SELECT_PICTOGRAMA)
      .eq("id_categorias", id_categoria)
      .eq("es_personalizado", false)
      .order("id_pictogramas", { ascending: true });

    if (generalesError) {
      return responderError(res, 500, generalesError.message);
    }

    if (!id_usuario) {
      return res.json({
        data: pictogramasGenerales,
        error: null
      });
    }

    const { data: relaciones, error: relacionesError } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario,
        id_pictogramas,
        pictogramas (
          id_pictogramas,
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        )
      `)
      .eq("id_usuario", id_usuario);

    if (relacionesError) {
      return responderError(res, 500, relacionesError.message);
    }

    const pictogramasPropios = relaciones
      .map((item) => item.pictogramas)
      .filter(Boolean)
      .filter((pictograma) => {
        return (
          pictograma.es_personalizado === true &&
          Number(pictograma.id_categorias) === Number(id_categoria)
        );
      });

    return res.json({
      data: [
        ...pictogramasGenerales,
        ...pictogramasPropios
      ],
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// POST /pictogramas
const crearPictograma = async (req, res) => {
  try {
    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body;

    if (!id_categorias || !nombre) {
      return responderError(res, 400, "Faltan datos obligatorios: id_categorias o nombre");
    }

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombrePictograma(nombreLimpio);

    if (errorNombre) {
      return responderError(res, 400, errorNombre);
    }

    const categoria = await obtenerCategoria(id_categorias);

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    const duplicado = await existePictogramaGeneralDuplicado({
      nombre: nombreLimpio,
      id_categorias
    });

    if (duplicado) {
      return responderError(res, 400, "Ya existe un pictograma general con ese nombre en esta categoría");
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre: nombreLimpio,
          imagen_url: imagen_url || null,
          audio_url: audio_url || null,
          es_personalizado: false
        }
      ])
      .select(SELECT_PICTOGRAMA)
      .single();

    if (error) {
      return responderError(res, 500, error.message);
    }

    return res.status(201).json({
      data,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// PUT /pictogramas/:id_pictograma
const actualizarPictograma = async (req, res) => {
  try {
    const { id_pictograma } = req.params;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body;

    const { data: pictogramaActual, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select(SELECT_PICTOGRAMA)
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (pictogramaError) {
      return responderError(res, 500, pictogramaError.message);
    }

    if (!pictogramaActual) {
      return responderError(res, 404, "Pictograma no encontrado");
    }

    if (pictogramaActual.es_personalizado) {
      return responderError(res, 403, "Este endpoint es solo para pictogramas generales");
    }

    const camposActualizar = {};

    if (id_categorias !== undefined) camposActualizar.id_categorias = id_categorias;

    if (nombre !== undefined) {
      const nombreLimpio = normalizarTexto(nombre);
      const errorNombre = validarNombrePictograma(nombreLimpio);

      if (errorNombre) {
        return responderError(res, 400, errorNombre);
      }

      camposActualizar.nombre = nombreLimpio;
    }

    if (imagen_url !== undefined) camposActualizar.imagen_url = imagen_url;
    if (audio_url !== undefined) camposActualizar.audio_url = audio_url;

    if (Object.keys(camposActualizar).length === 0) {
      return responderError(res, 400, "No enviaste campos para actualizar");
    }

    const categoriaFinal = id_categorias || pictogramaActual.id_categorias;
    const nombreFinal = camposActualizar.nombre || pictogramaActual.nombre;

    if (id_categorias !== undefined) {
      const categoria = await obtenerCategoria(id_categorias);

      if (!categoria) {
        return responderError(res, 404, "Categoría no encontrada");
      }
    }

    const duplicado = await existePictogramaGeneralDuplicado({
      nombre: nombreFinal,
      id_categorias: categoriaFinal,
      excluirId: id_pictograma
    });

    if (duplicado) {
      return responderError(res, 400, "Ya existe un pictograma general con ese nombre en esta categoría");
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .update(camposActualizar)
      .eq("id_pictogramas", id_pictograma)
      .select(SELECT_PICTOGRAMA)
      .single();

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

// DELETE /pictogramas/:id_pictograma
const eliminarPictograma = async (req, res) => {
  try {
    const { id_pictograma } = req.params;

    await supabase
      .from("tableros_pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    await supabase
      .from("usuarios_pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    await supabase
      .from("frase_pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    const { error } = await supabase
      .from("pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    if (error) {
      return responderError(res, 500, error.message);
    }

    return res.json({
      data: {
        mensaje: "Pictograma eliminado correctamente"
      },
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// POST /pictogramas/personalizado
const crearPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body;

    if (!id_categorias || !nombre) {
      return responderError(res, 400, "Faltan datos obligatorios: id_categorias o nombre");
    }

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombrePictograma(nombreLimpio);

    if (errorNombre) {
      return responderError(res, 400, errorNombre);
    }

    const categoria = await obtenerCategoria(id_categorias);

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    if (!usuarioPuedeUsarCategoria(categoria, id_usuario)) {
      return responderError(res, 403, "No tenés permiso para usar esta categoría");
    }

    const duplicado = await existePictogramaPersonalizadoDuplicado({
      id_usuario,
      nombre: nombreLimpio,
      id_categorias
    });

    if (duplicado) {
      return responderError(res, 400, "Ya tenés un pictograma con ese nombre en esta categoría");
    }

    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre: nombreLimpio,
          imagen_url: imagen_url || null,
          audio_url: audio_url || null,
          es_personalizado: true
        }
      ])
      .select(SELECT_PICTOGRAMA)
      .single();

    if (pictogramaError) {
      return responderError(res, 500, pictogramaError.message);
    }

    const { error: relacionError } = await supabase
      .from("usuarios_pictogramas")
      .insert([
        {
          id_usuario,
          id_pictogramas: pictogramaCreado.id_pictogramas
        }
      ]);

    if (relacionError) {
      await supabase
        .from("pictogramas")
        .delete()
        .eq("id_pictogramas", pictogramaCreado.id_pictogramas);

      return responderError(res, 500, relacionError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "crear_pictograma_personalizado",
      detalle: `Pictograma personalizado creado: ${nombreLimpio}`
    });

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// GET /pictogramas/mis-personalizados
const obtenerMisPictogramasPersonalizados = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario_pictograma,
        id_usuario,
        id_pictogramas,
        fecha_creacion,
        pictogramas (
          id_pictogramas,
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        )
      `)
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", { ascending: false });

    if (error) {
      return responderError(res, 500, error.message);
    }

    const pictogramas = data
      .map((item) => item.pictogramas)
      .filter(Boolean)
      .filter((pictograma) => pictograma.es_personalizado === true);

    return res.json({
      data: pictogramas,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// PUT /pictogramas/personalizado/:id_pictograma
const actualizarPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url
    } = req.body;

    const relacion = await verificarPictogramaPropio(id_usuario, id_pictograma);

    if (!relacion || !relacion.pictogramas) {
      return responderError(res, 404, "No se encontró un pictograma personalizado propio con ese ID");
    }

    const pictogramaActual = relacion.pictogramas;

    if (!pictogramaActual.es_personalizado) {
      return responderError(res, 400, "El pictograma no es personalizado");
    }

    const camposActualizar = {};

    if (id_categorias !== undefined) camposActualizar.id_categorias = id_categorias;

    if (nombre !== undefined) {
      const nombreLimpio = normalizarTexto(nombre);
      const errorNombre = validarNombrePictograma(nombreLimpio);

      if (errorNombre) {
        return responderError(res, 400, errorNombre);
      }

      camposActualizar.nombre = nombreLimpio;
    }

    if (imagen_url !== undefined) camposActualizar.imagen_url = imagen_url;
    if (audio_url !== undefined) camposActualizar.audio_url = audio_url;

    if (Object.keys(camposActualizar).length === 0) {
      return responderError(res, 400, "No enviaste campos para actualizar");
    }

    const categoriaFinal = id_categorias || pictogramaActual.id_categorias;
    const nombreFinal = camposActualizar.nombre || pictogramaActual.nombre;

    if (id_categorias !== undefined) {
      const categoria = await obtenerCategoria(id_categorias);

      if (!categoria) {
        return responderError(res, 404, "Categoría no encontrada");
      }

      if (!usuarioPuedeUsarCategoria(categoria, id_usuario)) {
        return responderError(res, 403, "No tenés permiso para usar esta categoría");
      }
    }

    const duplicado = await existePictogramaPersonalizadoDuplicado({
      id_usuario,
      nombre: nombreFinal,
      id_categorias: categoriaFinal,
      excluirId: id_pictograma
    });

    if (duplicado) {
      return responderError(res, 400, "Ya tenés un pictograma con ese nombre en esta categoría");
    }

    const { data: pictogramaActualizado, error: actualizarError } = await supabase
      .from("pictogramas")
      .update(camposActualizar)
      .eq("id_pictogramas", id_pictograma)
      .select(SELECT_PICTOGRAMA)
      .single();

    if (actualizarError) {
      return responderError(res, 500, actualizarError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "actualizar_pictograma_personalizado",
      detalle: `Pictograma personalizado actualizado: ${pictogramaActualizado.nombre}`
    });

    return res.json({
      data: pictogramaActualizado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

// DELETE /pictogramas/personalizado/:id_pictograma
const eliminarPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    const relacion = await verificarPictogramaPropio(id_usuario, id_pictograma);

    if (!relacion || !relacion.pictogramas) {
      return responderError(res, 404, "No se encontró un pictograma personalizado propio con ese ID");
    }

    const pictograma = relacion.pictogramas;

    if (!pictograma.es_personalizado) {
      return responderError(res, 400, "El pictograma no es personalizado");
    }

    await supabase
      .from("tableros_pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    const { error: borrarRelacionError } = await supabase
      .from("usuarios_pictogramas")
      .delete()
      .eq("id_usuario", id_usuario)
      .eq("id_pictogramas", id_pictograma);

    if (borrarRelacionError) {
      return responderError(res, 500, borrarRelacionError.message);
    }

    const { data: otrasRelaciones, error: otrasRelacionesError } = await supabase
      .from("usuarios_pictogramas")
      .select("id_usuario_pictograma")
      .eq("id_pictogramas", id_pictograma);

    if (otrasRelacionesError) {
      return responderError(res, 500, otrasRelacionesError.message);
    }

    if (!otrasRelaciones || otrasRelaciones.length === 0) {
      const { error: borrarPictogramaError } = await supabase
        .from("pictogramas")
        .delete()
        .eq("id_pictogramas", id_pictograma);

      if (borrarPictogramaError) {
        return responderError(res, 500, borrarPictogramaError.message);
      }
    }

    await registrarHistorial({
      id_usuario,
      accion: "eliminar_pictograma_personalizado",
      detalle: `Pictograma personalizado eliminado: ${pictograma.nombre}`
    });

    return res.json({
      data: {
        mensaje: "Pictograma personalizado eliminado correctamente"
      },
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

const crearPictogramaPersonalizadoConImagen = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      audio_url
    } = req.body;

    if (!id_categorias || !nombre) {
      return responderError(res, 400, "Faltan datos obligatorios: id_categorias y nombre");
    }

    if (!req.file) {
      return responderError(res, 400, "Tenés que enviar una imagen en el campo imagen");
    }

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombrePictograma(nombreLimpio);

    if (errorNombre) {
      return responderError(res, 400, errorNombre);
    }

    const categoria = await obtenerCategoria(id_categorias);

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    if (!usuarioPuedeUsarCategoria(categoria, id_usuario)) {
      return responderError(res, 403, "No tenés permiso para usar esta categoría");
    }

    const duplicado = await existePictogramaPersonalizadoDuplicado({
      id_usuario,
      nombre: nombreLimpio,
      id_categorias
    });

    if (duplicado) {
      return responderError(res, 400, "Ya tenés un pictograma con ese nombre en esta categoría");
    }

    const imagen_url = await subirImagenPictograma({
      archivo: req.file,
      carpeta: String(id_usuario),
      nombreBase: `pictograma-${id_usuario}`
    });

    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre: nombreLimpio,
          imagen_url,
          audio_url: audio_url || null,
          es_personalizado: true
        }
      ])
      .select(SELECT_PICTOGRAMA)
      .single();

    if (pictogramaError) {
      return responderError(res, 500, pictogramaError.message);
    }

    const { error: relacionError } = await supabase
      .from("usuarios_pictogramas")
      .insert([
        {
          id_usuario,
          id_pictogramas: pictogramaCreado.id_pictogramas
        }
      ]);

    if (relacionError) {
      await supabase
        .from("pictogramas")
        .delete()
        .eq("id_pictogramas", pictogramaCreado.id_pictogramas);

      return responderError(res, 500, relacionError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "crear_pictograma_con_imagen",
      detalle: `Pictograma personalizado creado con imagen: ${nombreLimpio}`
    });

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

const actualizarImagenPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!req.file) {
      return responderError(res, 400, "Tenés que enviar una imagen en el campo imagen");
    }

    const relacion = await verificarPictogramaPropio(id_usuario, id_pictograma);

    if (!relacion || !relacion.pictogramas) {
      return responderError(res, 404, "No se encontró un pictograma personalizado propio con ese ID");
    }

    if (!relacion.pictogramas.es_personalizado) {
      return responderError(res, 403, "Solo se puede actualizar la imagen de pictogramas personalizados");
    }

    const imagen_url = await subirImagenPictograma({
      archivo: req.file,
      carpeta: String(id_usuario),
      nombreBase: `pictograma-${id_usuario}-${id_pictograma}`
    });

    const { data: pictogramaActualizado, error: updateError } = await supabase
      .from("pictogramas")
      .update({ imagen_url })
      .eq("id_pictogramas", id_pictograma)
      .select(SELECT_PICTOGRAMA)
      .single();

    if (updateError) {
      return responderError(res, 500, updateError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "actualizar_imagen_pictograma",
      detalle: `Imagen actualizada para pictograma: ${pictogramaActualizado.nombre}`
    });

    return res.json({
      data: pictogramaActualizado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

const crearPictogramaConImagen = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      audio_url
    } = req.body;

    if (!id_categorias || !nombre) {
      return responderError(res, 400, "Faltan datos obligatorios: id_categorias y nombre");
    }

    if (!req.file) {
      return responderError(res, 400, "Tenés que enviar una imagen en el campo imagen");
    }

    const nombreLimpio = normalizarTexto(nombre);
    const errorNombre = validarNombrePictograma(nombreLimpio);

    if (errorNombre) {
      return responderError(res, 400, errorNombre);
    }

    const categoria = await obtenerCategoria(id_categorias);

    if (!categoria) {
      return responderError(res, 404, "Categoría no encontrada");
    }

    const duplicado = await existePictogramaGeneralDuplicado({
      nombre: nombreLimpio,
      id_categorias
    });

    if (duplicado) {
      return responderError(res, 400, "Ya existe un pictograma general con ese nombre en esta categoría");
    }

    const imagen_url = await subirImagenPictograma({
      archivo: req.file,
      carpeta: "generales",
      nombreBase: "general"
    });

    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre: nombreLimpio,
          imagen_url,
          audio_url: audio_url || null,
          es_personalizado: false
        }
      ])
      .select(SELECT_PICTOGRAMA)
      .single();

    if (pictogramaError) {
      return responderError(res, 500, pictogramaError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "crear_pictograma_general_con_imagen",
      detalle: `Pictograma general creado con imagen: ${nombreLimpio}`
    });

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

const actualizarImagenPictogramaGeneral = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!req.file) {
      return responderError(res, 400, "Tenés que enviar una imagen en el campo imagen");
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select(SELECT_PICTOGRAMA)
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (pictogramaError) {
      return responderError(res, 500, pictogramaError.message);
    }

    if (!pictograma) {
      return responderError(res, 404, "Pictograma no encontrado");
    }

    if (pictograma.es_personalizado) {
      return responderError(res, 403, "Este endpoint es solo para pictogramas generales");
    }

    const imagen_url = await subirImagenPictograma({
      archivo: req.file,
      carpeta: "generales",
      nombreBase: `general-${id_pictograma}`
    });

    const { data: pictogramaActualizado, error: updateError } = await supabase
      .from("pictogramas")
      .update({ imagen_url })
      .eq("id_pictogramas", id_pictograma)
      .select(SELECT_PICTOGRAMA)
      .single();

    if (updateError) {
      return responderError(res, 500, updateError.message);
    }

    await registrarHistorial({
      id_usuario,
      accion: "actualizar_imagen_pictograma_general",
      detalle: `Imagen actualizada para pictograma general: ${pictogramaActualizado.nombre}`
    });

    return res.json({
      data: pictogramaActualizado,
      error: null
    });

  } catch (error) {
    return responderError(res, 500, error.message);
  }
};

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