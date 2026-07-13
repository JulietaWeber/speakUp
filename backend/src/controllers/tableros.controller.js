const supabase = require("../config/Supabase");

const obtenerMisTableros = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data, error } = await supabase
      .from("tableros")
      .select("id_tablero, id_usuario, nombre, color, icono, es_publico, fecha_creacion")
      .eq("id_usuario", id_usuario)
      .order("fecha_creacion", { ascending: false });

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

const crearTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { nombre, color, icono, es_publico } = req.body;

    if (!nombre) {
      return res.status(400).json({
        data: null,
        error: "El nombre del tablero es obligatorio"
      });
    }

    const { data, error } = await supabase
      .from("tableros")
      .insert([
        {
          id_usuario,
          nombre,
          color: color || "#FFFFFF",
          icono: icono || null,
          es_publico: es_publico || false
        }
      ])
      .select("id_tablero, id_usuario, nombre, color, icono, es_publico, fecha_creacion")
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
        accion: "crear_tablero",
        detalle: `Tablero creado: ${nombre}`
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

const obtenerPictogramasDeTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero } = req.params;

    const { data: tablero, error: tableroError } = await supabase
      .from("tableros")
      .select("id_tablero, id_usuario")
      .eq("id_tablero", id_tablero)
      .maybeSingle();

    if (tableroError) {
      return res.status(500).json({
        data: null,
        error: tableroError.message
      });
    }

    if (!tablero) {
      return res.status(404).json({
        data: null,
        error: "Tablero no encontrado"
      });
    }

    if (tablero.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para ver este tablero"
      });
    }

    const { data, error } = await supabase
      .from("tableros_pictogramas")
      .select(`
        id_tablero_pictogramas,
        id_tablero,
        id_pictogramas,
        posicion_x,
        posicion_y,
        pictogramas (
          id_pictogramas,
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        )
      `)
      .eq("id_tablero", id_tablero)
      .order("posicion_y", { ascending: true })
      .order("posicion_x", { ascending: true });

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

const agregarPictogramaATablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero } = req.params;
    const { id_pictogramas, posicion_x, posicion_y } = req.body;

    if (!id_pictogramas) {
      return res.status(400).json({
        data: null,
        error: "Falta id_pictogramas"
      });
    }

    const { data: tablero, error: tableroError } = await supabase
      .from("tableros")
      .select("id_tablero, id_usuario")
      .eq("id_tablero", id_tablero)
      .maybeSingle();

    if (tableroError) {
      return res.status(500).json({
        data: null,
        error: tableroError.message
      });
    }

    if (!tablero) {
      return res.status(404).json({
        data: null,
        error: "Tablero no encontrado"
      });
    }

    if (tablero.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para modificar este tablero"
      });
    }

    const { data: pictograma, error: pictogramaError } = await supabase
      .from("pictogramas")
      .select("id_pictogramas, nombre")
      .eq("id_pictogramas", id_pictogramas)
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

    const { data, error } = await supabase
      .from("tableros_pictogramas")
      .insert([
        {
          id_tablero,
          id_pictogramas,
          posicion_x: posicion_x || 0,
          posicion_y: posicion_y || 0
        }
      ])
      .select()
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
        accion: "agregar_pictograma_tablero",
        detalle: `Pictograma agregado al tablero: ${pictograma.nombre}`
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

const eliminarPictogramaDeTablero = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;
    const { id_tablero, id_pictogramas } = req.params;

    const { data: tablero, error: tableroError } = await supabase
      .from("tableros")
      .select("id_tablero, id_usuario")
      .eq("id_tablero", id_tablero)
      .maybeSingle();

    if (tableroError) {
      return res.status(500).json({
        data: null,
        error: tableroError.message
      });
    }

    if (!tablero) {
      return res.status(404).json({
        data: null,
        error: "Tablero no encontrado"
      });
    }

    if (tablero.id_usuario !== id_usuario) {
      return res.status(403).json({
        data: null,
        error: "No tenés permiso para modificar este tablero"
      });
    }

    const { error } = await supabase
      .from("tableros_pictogramas")
      .delete()
      .eq("id_tablero", id_tablero)
      .eq("id_pictogramas", id_pictogramas);

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    await supabase.from("historial_uso").insert([
      {
        id_usuario,
        accion: "eliminar_pictograma_tablero",
        detalle: `Pictograma eliminado del tablero ${id_tablero}`
      }
    ]);

    return res.json({
      data: {
        mensaje: "Pictograma eliminado del tablero"
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
  obtenerMisTableros,
  crearTablero,
  obtenerPictogramasDeTablero,
  agregarPictogramaATablero,
  eliminarPictogramaDeTablero
};