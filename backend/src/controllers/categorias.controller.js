const supabase = require("../config/Supabase");

// GET /categorias
const obtenerCategorias = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;

    let query = supabase
      .from("categorias")
      .select("id_categorias, nombre, color, id_usuario, es_personalizada")
      .order("id_categorias", { ascending: true });

    if (id_usuario) {
      query = query.or(`id_usuario.is.null,id_usuario.eq.${id_usuario}`);
    } else {
      query = query.is("id_usuario", null);
    }

    const { data, error } = await query;

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

// GET /categorias/:id_categoria
const obtenerCategoriaPorId = async (req, res) => {
  try {
    const id_usuario = req.usuario?.id_usuario || null;
    const { id_categoria } = req.params;

    const { data: categoria, error } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, color, id_usuario, es_personalizada")
      .eq("id_categorias", id_categoria)
      .maybeSingle();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    if (!categoria) {
      return res.status(404).json({
        data: null,
        error: "Categoría no encontrada"
      });
    }

    const esGeneral = categoria.id_usuario === null;
    const esPropia = Number(categoria.id_usuario) === Number(id_usuario);

    if (!esGeneral && !esPropia) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para ver esta categoría"
      });
    }

    return res.json({
      data: categoria,
      error: null
    });

  } catch (error) {
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// POST /categorias
const crearCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { nombre, color } = req.body;

    if (!nombre) {
      return res.status(400).json({
        data: null,
        error: "Falta el nombre de la categoría"
      });
    }

    const { data, error } = await supabase
      .from("categorias")
      .insert([
        {
          nombre,
          color: color || null,
          id_usuario,
          es_personalizada: true
        }
      ])
      .select("id_categorias, nombre, color, id_usuario, es_personalizada")
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "crear_categoria",
        detalle: `Categoría creada: ${nombre}`
      }
    ]);

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

// PUT /categorias/:id_categoria
const actualizarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_categoria } = req.params;
    const { nombre, color } = req.body;

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, id_usuario, es_personalizada")
      .eq("id_categorias", id_categoria)
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

    // Las categorías default tienen id_usuario = null.
    // El usuario común no puede editarlas.
    if (categoria.id_usuario === null || categoria.es_personalizada === false) {
      return res.status(403).json({
        data: null,
        error: "No se puede modificar una categoría default del sistema"
      });
    }

    // Solo el dueño puede editar su categoría personal.
    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para modificar esta categoría"
      });
    }

    const camposActualizar = {};

    if (nombre !== undefined) camposActualizar.nombre = nombre;
    if (color !== undefined) camposActualizar.color = color;

    if (Object.keys(camposActualizar).length === 0) {
      return res.status(400).json({
        data: null,
        error: "No enviaste campos para actualizar"
      });
    }

    const { data, error } = await supabase
      .from("categorias")
      .update(camposActualizar)
      .eq("id_categorias", id_categoria)
      .select("id_categorias, nombre, color, id_usuario, es_personalizada")
      .single();

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
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
    return res.status(500).json({
      data: null,
      error: error.message
    });
  }
};

// DELETE /categorias/:id_categoria
const eliminarCategoria = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_categoria } = req.params;

    const { data: categoria, error: categoriaError } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, id_usuario, es_personalizada")
      .eq("id_categorias", id_categoria)
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

    // Las categorías default no se pueden borrar.
    if (categoria.id_usuario === null || categoria.es_personalizada === false) {
      return res.status(403).json({
        data: null,
        error: "No se puede eliminar una categoría default del sistema"
      });
    }

    // Solo el dueño puede borrar su categoría personal.
    if (Number(categoria.id_usuario) !== Number(id_usuario)) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para eliminar esta categoría"
      });
    }

    const { data: pictogramasAsociados, error: pictogramasError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas")
      .eq("id_categorias", id_categoria);

    if (pictogramasError) {
      return res.status(500).json({
        data: null,
        error: pictogramasError.message
      });
    }

    if (pictogramasAsociados && pictogramasAsociados.length > 0) {
      return res.status(400).json({
        data: null,
        error: "No se puede eliminar la categoría porque tiene pictogramas asociados"
      });
    }

    const { error } = await supabase
      .from("categorias")
      .delete()
      .eq("id_categorias", id_categoria);

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
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
        mensaje: "Categoría eliminada correctamente"
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

const obtenerMisCategorias = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("categorias")
      .select("id_categorias, nombre, color, id_usuario, es_personalizada")
      .or(`id_usuario.is.null,id_usuario.eq.${id_usuario}`)
      .order("id_categorias", { ascending: true });

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

module.exports = {
  obtenerCategorias,
  obtenerCategoriaPorId,
  obtenerMisCategorias,
  crearCategoria,
  actualizarCategoria,
  eliminarCategoria
};