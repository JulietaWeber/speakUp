const supabase = require("../config/Supabase");

const obtenerMiHistorial = async (req, res) => {
  try {
    const id_usuario = req.usuario.id_usuario;

    const { data: historial, error } = await supabase
      .from("historial_uso")
      .select("id_historial, id_usuario, accion, detalle, fecha")
      .eq("id_usuario", id_usuario)
      .order("fecha", { ascending: false });

    if (error) {
      return res.status(500).json({
        data: null,
        error: error.message
      });
    }

    return res.json({
      data: historial,
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
  obtenerMiHistorial
};