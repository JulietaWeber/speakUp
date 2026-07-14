const supabase = require("../config/Supabase");

const obtenerPictogramas = async (req, res) => {
  try {
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
  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

const obtenerPictogramasPorCategoria = async (req, res) => {
  try {
    const { id_categoria } = req.params;

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
  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};


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


const eliminarPictograma = async (req, res) => {
  try {
    const { id_pictograma } = req.params;

    // Primero borro relaciones donde pueda aparecer.
    // Esto evita errores de foreign key en desarrollo.
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
      // Si falla la relación, borro el pictograma recién creado para no dejar basura.
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

    // Borro primero de tableros por si el usuario lo había agregado a alguno.
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

module.exports = {
  obtenerPictogramas,
  obtenerPictogramasPorCategoria,
  crearPictograma,
  actualizarPictograma,
  eliminarPictograma,
  crearPictogramaPersonalizado,
  obtenerMisPictogramasPersonalizados,
  eliminarPictogramaPersonalizado
};