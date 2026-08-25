const supabase = require("../config/Supabase");
const supabaseAdmin = require("../config/SupabaseAdmin");

// GET /pictogramas
// GET /pictogramas
const obtenerPictogramas = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const rol = req.usuario?.rol || null;

    // Si es admin, puede ver todos los pictogramas
    if (rol === "admin") {
      const { data, error } = await supabase
        .from("pictogramas")
        .select(
          "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
        )
        .order("id_pictogramas", { ascending: true });

      if (error) {
        return res.status(500).json({
          data: null,
          error: error.message
        });
      }

      return res.json({
        data,
        error: null
      });
    }

    // Pictogramas generales/default
    const { data: pictogramasGenerales, error: generalesError } = await supabase
      .from("pictogramas")
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .eq("es_personalizado", false)
      .order("id_pictogramas", { ascending: true });

    if (generalesError) {
      return res.status(500).json({
        data: null,
        error: generalesError.message
      });
    }

    // Si no hay usuario logueado, solo devuelve generales
    if (!id_usuario) {
      return res.json({
        data: pictogramasGenerales,
        error: null
      });
    }

    // Pictogramas personalizados propios
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
      return res.status(500).json({
        data: null,
        error: relacionesError.message
      });
    }

    const pictogramasPropios = relaciones
      .map((item) => item.pictogramas)
      .filter(Boolean);

    return res.json({
      data: [
        ...pictogramasGenerales,
        ...pictogramasPropios
      ],
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// GET /pictogramas/categoria/:id_categoria
// GET /pictogramas/categoria/:id_categoria
const obtenerPictogramasPorCategoria = async (req, res) => {
  try {
    const { id_categoria } = req.params;
    const id_usuario = req.usuario?.id_usuario || null;
    const rol = req.usuario?.rol || null;

    // Admin ve todos los pictogramas de la categoría
    if (rol === "admin") {
      const { data, error } = await supabase
        .from("pictogramas")
        .select(
          "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
        )
        .eq("id_categorias", id_categoria)
        .order("id_pictogramas", { ascending: true });

      if (error) {
        return res.status(500).json({
          data: null,
          error: error.message
        });
      }

      return res.json({
        data,
        error: null
      });
    }

    // Generales/default de esa categoría
    const { data: pictogramasGenerales, error: generalesError } = await supabase
      .from("pictogramas")
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .eq("id_categorias", id_categoria)
      .eq("es_personalizado", false)
      .order("id_pictogramas", { ascending: true });

    if (generalesError) {
      return res.status(500).json({
        data: null,
        error: generalesError.message
      });
    }

    if (!id_usuario) {
      return res.json({
        data: pictogramasGenerales,
        error: null
      });
    }

    // Personalizados propios de esa categoría
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
      return res.status(500).json({
        data: null,
        error: relacionesError.message
      });
    }

    const pictogramasPropios = relaciones
      .map((item) => item.pictogramas)
      .filter(Boolean)
      .filter((pictograma) => {
        return Number(pictograma.id_categorias) === Number(id_categoria);
      });

    return res.json({
      data: [
        ...pictogramasGenerales,
        ...pictogramasPropios
      ],
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /pictogramas
// Pictograma general del sistema. Esta ruta debería estar protegida con verificarAdmin.
const crearPictograma = async (req, res) => {
  try {
    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url,
      es_personalizado
    } = req.body;

    if (!id_categorias || !nombre) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: id_categorias o nombre"
      });
    }

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias")
      .eq("id_categorias", id_categorias)
      .maybeSingle();

    if (categoriaError) {
      return res.status(500).json({
        data: null,
        error: categoriaError.message
      });
    }

    if (!categoria) {
      return res.status(404).json({
        data: null,
        error: "Categoría no encontrada"
      });
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre,
          imagen_url: imagen_url || null,
          audio_url: audio_url || null,
          es_personalizado: es_personalizado || false
        }
      ])
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.status(201).json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// PUT /pictogramas/:id_pictograma
// Pictograma general del sistema. Esta ruta debería estar protegida con verificarAdmin.
const actualizarPictograma = async (req, res) => {
  try {
    const { id_pictograma } = req.params;

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url,
      es_personalizado
    } = req.body;

    const camposActualizar = {};

    if (id_categorias !== undefined) camposActualizar.id_categorias = id_categorias;
    if (nombre !== undefined) camposActualizar.nombre = nombre;
    if (imagen_url !== undefined) camposActualizar.imagen_url = imagen_url;
    if (audio_url !== undefined) camposActualizar.audio_url = audio_url;
    if (es_personalizado !== undefined) camposActualizar.es_personalizado = es_personalizado;

    if (Object.keys(camposActualizar).length === 0) {
      return res.status(400).json({
        data: null,
        error: "No enviaste campos para actualizar"
      });
    }

    if (id_categorias !== undefined) {
      const { data: categoria, error: categoriaError } = await supabase
        .from("categorias")
        .select("id_categorias")
        .eq("id_categorias", id_categorias)
        .maybeSingle();

      if (categoriaError) {
        return res.status(500).json({
          data: null,
          error: categoriaError.message
        });
      }

      if (!categoria) {
        return res.status(404).json({
          data: null,
          error: "Categoría no encontrada"
        });
      }
    }

    const { data, error } = await supabase
      .from("pictogramas")
      .update(camposActualizar)
      .eq("id_pictogramas", id_pictograma)
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// DELETE /pictogramas/:id_pictograma
// Pictograma general del sistema. Esta ruta debería estar protegida con verificarAdmin.
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

    const { error } = await supabase
      .from("pictogramas")
      .delete()
      .eq("id_pictogramas", id_pictograma);

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data: {
        mensaje: "Pictograma eliminado correctamente"
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
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: id_categorias o nombre"
      });
    }

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, id_usuario, es_personalizada")
      .eq("id_categorias", id_categorias)
      .maybeSingle();

    if (categoriaError) {
      return res.status(500).json({
        data: null,
        error: categoriaError.message
      });
    }

    if (!categoria) {
      return res.status(404).json({
        data: null,
        error: "Categoría no encontrada"
      });
    }

    const categoriaEsDefault =
      categoria.id_usuario === null || categoria.es_personalizada === false;

    const categoriaEsPropia =
      Number(categoria.id_usuario) === Number(id_usuario);

    if (!categoriaEsDefault && !categoriaEsPropia) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para usar esta categoría"
      });
    }

    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre,
          imagen_url: imagen_url || null,
          audio_url: audio_url || null,
          es_personalizado: true
        }
      ])
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .single();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
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

      return res.status(500).json({
        data: null,
        error: relacionError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_pictograma_personalizado",
        detalle: `Pictograma personalizado creado: ${nombre}`
      }
    ]);

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
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
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    const pictogramas = data
      .map((item) => item.pictogramas)
      .filter(Boolean);

    return res.json({
      data: pictogramas,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
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

    const { data: relacion, error: relacionError } = await supabase
      .from("usuarios_pictogramas")
      .select("id_usuario_pictograma, id_usuario, id_pictogramas")
      .eq("id_usuario", id_usuario)
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (relacionError) {
      return res.status(500).json({
        data: null,
        error: relacionError.message
      });
    }

    if (!relacion) {
      return res.status(404).json({
        data: null,
        error: "No se encontró un pictograma personalizado propio con ese ID"
      });
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, es_personalizado")
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
    }

    if (!pictograma || !pictograma.es_personalizado) {
      return res.status(400).json({
        data: null,
        error: "El pictograma no es personalizado"
      });
    }

    const camposActualizar = {};

    if (id_categorias !== undefined) camposActualizar.id_categorias = id_categorias;
    if (nombre !== undefined) camposActualizar.nombre = nombre;
    if (imagen_url !== undefined) camposActualizar.imagen_url = imagen_url;
    if (audio_url !== undefined) camposActualizar.audio_url = audio_url;

    if (Object.keys(camposActualizar).length === 0) {
      return res.status(400).json({
        data: null,
        error: "No enviaste campos para actualizar"
      });
    }

    if (id_categorias !== undefined) {
      const { data: categoria, error: categoriaError } = await supabase
        .from("categorias")
        .select("id_categorias, nombre, id_usuario, es_personalizada")
        .eq("id_categorias", id_categorias)
        .maybeSingle();

      if (categoriaError) {
        return res.status(500).json({
          data: null,
          error: categoriaError.message
        });
      }

      if (!categoria) {
        return res.status(404).json({
          data: null,
          error: "Categoría no encontrada"
        });
      }

      const categoriaEsDefault =
        categoria.id_usuario === null || categoria.es_personalizada === false;

      const categoriaEsPropia =
        Number(categoria.id_usuario) === Number(id_usuario);

      if (!categoriaEsDefault && !categoriaEsPropia) {
        return res.status(403).json({
          data: null,
          error: "No tenés permiso para usar esta categoría"
        });
      }
    }

    const { data: pictogramaActualizado, error: actualizarError } = await supabase
      .from("pictogramas")
      .update(camposActualizar)
      .eq("id_pictogramas", id_pictograma)
      .select(
        "id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado"
      )
      .single();

    if (actualizarError) {
      return res.status(500).json({
        data: null,
        error: actualizarError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "actualizar_pictograma_personalizado",
        detalle: `Pictograma personalizado actualizado: ${pictogramaActualizado.nombre}`
      }
    ]);

    return res.json({
      data: pictogramaActualizado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// DELETE /pictogramas/personalizado/:id_pictograma
const eliminarPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    const { data: relacion, error: relacionBuscarError } = await supabase
      .from("usuarios_pictogramas")
      .select("id_usuario_pictograma, id_usuario, id_pictogramas")
      .eq("id_usuario", id_usuario)
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (relacionBuscarError) {
      return res.status(500).json({
        data: null,
        error: relacionBuscarError.message
      });
    }

    if (!relacion) {
      return res.status(404).json({
        data: null,
        error: "No se encontró un pictograma personalizado propio con ese ID"
      });
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre, es_personalizado")
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
    }

    if (!pictograma || !pictograma.es_personalizado) {
      return res.status(400).json({
        data: null,
        error: "El pictograma no es personalizado"
      });
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
      return res.status(500).json({
        data: null,
        error: borrarRelacionError.message
      });
    }

    const { data: otrasRelaciones, error: otrasRelacionesError } = await supabase
      .from("usuarios_pictogramas")
      .select("id_usuario_pictograma")
      .eq("id_pictogramas", id_pictograma);

    if (otrasRelacionesError) {
      return res.status(500).json({
        data: null,
        error: otrasRelacionesError.message
      });
    }

    if (!otrasRelaciones || otrasRelaciones.length === 0) {
      const { error: borrarPictogramaError } = await supabase
        .from("pictogramas")
        .delete()
        .eq("id_pictogramas", id_pictograma);

      if (borrarPictogramaError) {
        return res.status(500).json({
          data: null,
          error: borrarPictogramaError.message
        });
      }
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "eliminar_pictograma_personalizado",
        detalle: `Pictograma personalizado eliminado: ${pictograma.nombre}`
      }
    ]);

    return res.json({
      data: {
        mensaje: "Pictograma personalizado eliminado correctamente"
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

const crearPictogramaPersonalizadoConImagen = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const {
      id_categorias,
      nombre,
      audio_url
    } = req.body;

    if (!id_categorias || !nombre) {
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: id_categorias y nombre"
      });
    }

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo imagen"
      });
    }

    // Validar que la categoría exista
    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, id_usuario, es_personalizada")
      .eq("id_categorias", id_categorias)
      .maybeSingle();

    if (categoriaError) {
      return res.status(500).json({
        data: null,
        error: categoriaError.message
      });
    }

    if (!categoria) {
      return res.status(404).json({
        data: null,
        error: "Categoría no encontrada"
      });
    }

    const categoriaEsDefault =
      categoria.id_usuario === null || categoria.es_personalizada === false;

    const categoriaEsPropia =
      Number(categoria.id_usuario) === Number(id_usuario);

    if (!categoriaEsDefault && !categoriaEsPropia) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para usar esta categoría"
      });
    }

    // Preparar extensión
    let extension = req.file.originalname
      .split(".")
      .pop()
      .toLowerCase();

    if (extension === "jfif" || extension === "jpeg") {
      extension = "jpg";
    }

    const nombreArchivo = `pictograma-${id_usuario}-${Date.now()}.${extension}`;
    const rutaArchivo = `${id_usuario}/${nombreArchivo}`;

    // Subir imagen a Supabase Storage
    const { error: uploadError } = await supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: true
      });

    if (uploadError) {
      return res.status(500).json({
        data: null,
        error: uploadError.message
      });
    }

    const { data: publicUrlData } = supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .getPublicUrl(rutaArchivo);

    const imagen_url = publicUrlData.publicUrl;

    // Crear pictograma personalizado
    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre,
          imagen_url,
          audio_url: audio_url || null,
          es_personalizado: true
        }
      ])
      .select("*")
      .single();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
    }

    // Relacionar pictograma con usuario
    const { error: relacionError } = await supabase
      .from("usuarios_pictogramas")
      .insert([
        {
          id_usuario,
          id_pictogramas: pictogramaCreado.id_pictogramas
        }
      ]);

    if (relacionError) {
      return res.status(500).json({
        data: null,
        error: relacionError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_pictograma_con_imagen",
        detalle: `Pictograma personalizado creado con imagen: ${nombre}`
      }
    ]);

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const actualizarImagenPictogramaPersonalizado = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo imagen"
      });
    }

    // Verificar que el pictograma pertenezca al usuario
    const { data: relacion, error: relacionError } = await supabase
      .from("usuarios_pictogramas")
      .select(`
        id_usuario,
        id_pictogramas,
        pictogramas (
          id_pictogramas,
          nombre,
          imagen_url,
          es_personalizado
        )
      `)
      .eq("id_usuario", id_usuario)
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (relacionError) {
      return res.status(500).json({
        data: null,
        error: relacionError.message
      });
    }

    if (!relacion || !relacion.pictogramas) {
      return res.status(404).json({
        data: null,
        error: "No se encontró un pictograma personalizado propio con ese ID"
      });
    }

    if (!relacion.pictogramas.es_personalizado) {
      return res.status(403).json({
        data: null,
        error: "Solo se puede actualizar la imagen de pictogramas personalizados"
      });
    }

    let extension = req.file.originalname
      .split(".")
      .pop()
      .toLowerCase();

    if (extension === "jfif" || extension === "jpeg") {
      extension = "jpg";
    }

    const nombreArchivo = `pictograma-${id_usuario}-${id_pictograma}-${Date.now()}.${extension}`;
    const rutaArchivo = `${id_usuario}/${nombreArchivo}`;

    const { error: uploadError } = await supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: true
      });

    if (uploadError) {
      return res.status(500).json({
        data: null,
        error: uploadError.message
      });
    }

    const { data: publicUrlData } = supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .getPublicUrl(rutaArchivo);

    const imagen_url = publicUrlData.publicUrl;

    const { data: pictogramaActualizado, error: updateError } = await supabase
      .from("pictogramas")
      .update({ imagen_url })
      .eq("id_pictogramas", id_pictograma)
      .select("id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado")
      .single();

    if (updateError) {
      return res.status(500).json({
        data: null,
        error: updateError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "actualizar_imagen_pictograma",
        detalle: `Imagen actualizada para pictograma: ${pictogramaActualizado.nombre}`
      }
    ]);

    return res.json({
      data: pictogramaActualizado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
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
      return res.status(400).json({
        data: null,
        error: "Faltan datos obligatorios: id_categorias y nombre"
      });
    }

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo imagen"
      });
    }

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias, nombre")
      .eq("id_categorias", id_categorias)
      .maybeSingle();

    if (categoriaError) {
      return res.status(500).json({
        data: null,
        error: categoriaError.message
      });
    }

    if (!categoria) {
      return res.status(404).json({
        data: null,
        error: "Categoría no encontrada"
      });
    }

    let extension = req.file.originalname
      .split(".")
      .pop()
      .toLowerCase();

    if (extension === "jfif" || extension === "jpeg") {
      extension = "jpg";
    }

    const nombreArchivo = `general-${Date.now()}.${extension}`;
    const rutaArchivo = `generales/${nombreArchivo}`;

    const { error: uploadError } = await supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: true
      });

    if (uploadError) {
      return res.status(500).json({
        data: null,
        error: uploadError.message
      });
    }

    const { data: publicUrlData } = supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .getPublicUrl(rutaArchivo);

    const imagen_url = publicUrlData.publicUrl;

    const { data: pictogramaCreado, error: pictogramaError } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre,
          imagen_url,
          audio_url: audio_url || null,
          es_personalizado: false
        }
      ])
      .select("id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado")
      .single();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_pictograma_general_con_imagen",
        detalle: `Pictograma general creado con imagen: ${nombre}`
      }
    ]);

    return res.status(201).json({
      data: pictogramaCreado,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const actualizarImagenPictogramaGeneral = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_pictograma } = req.params;

    if (!req.file) {
      return res.status(400).json({
        data: null,
        error: "Tenés que enviar una imagen en el campo imagen"
      });
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre, imagen_url, es_personalizado")
      .eq("id_pictogramas", id_pictograma)
      .maybeSingle();

    if (pictogramaError) {
      return res.status(500).json({
        data: null,
        error: pictogramaError.message
      });
    }

    if (!pictograma) {
      return res.status(404).json({
        data: null,
        error: "Pictograma no encontrado"
      });
    }

    if (pictograma.es_personalizado) {
      return res.status(403).json({
        data: null,
        error: "Este endpoint es solo para pictogramas generales"
      });
    }

    let extension = req.file.originalname
      .split(".")
      .pop()
      .toLowerCase();

    if (extension === "jfif" || extension === "jpeg") {
      extension = "jpg";
    }

    const nombreArchivo = `general-${id_pictograma}-${Date.now()}.${extension}`;
    const rutaArchivo = `generales/${nombreArchivo}`;

    const { error: uploadError } = await supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .upload(rutaArchivo, req.file.buffer, {
        contentType: req.file.mimetype,
        upsert: true
      });

    if (uploadError) {
      return res.status(500).json({
        data: null,
        error: uploadError.message
      });
    }

    const { data: publicUrlData } = supabaseAdmin.storage
      .from("pictogramas-imagenes")
      .getPublicUrl(rutaArchivo);

    const imagen_url = publicUrlData.publicUrl;

    const { data: pictogramaActualizado, error: updateError } = await supabase
      .from("pictogramas")
      .update({ imagen_url })
      .eq("id_pictogramas", id_pictograma)
      .select("id_pictogramas, id_categorias, nombre, imagen_url, audio_url, es_personalizado")
      .single();

    if (updateError) {
      return res.status(500).json({
        data: null,
        error: updateError.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "actualizar_imagen_pictograma_general",
        detalle: `Imagen actualizada para pictograma general: ${pictogramaActualizado.nombre}`
      }
    ]);

    return res.json({
      data: pictogramaActualizado,
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