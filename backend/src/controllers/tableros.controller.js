const supabase = require("../config/Supabase");

const obtenerTableros = async (req, res) => {

  const { data, error } = await supabase
    .from("tableros")
    .select("*");

  res.json({ data, error });

};

const crearTablero = async (req, res) => {

    const {
      id_usuario,
      nombre,
      color,
      icono,
      es_publico
    } = req.body;
  
    const { data, error } = await supabase
      .from("tableros")
      .insert([
        {
          id_usuario,
          nombre,
          color,
          icono,
          es_publico
        }
      ]);
  
    res.json({
      data,
      error
    });
  
  };

  const obtenerTableroPorId = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("tableros")
      .select("*")
      .eq("id_tablero", id)
      .single();
  
    res.json({ data, error });
  
  };

  const actualizarTablero = async (req, res) => {

    const { id } = req.params;
  
    const {
      nombre,
      color,
      icono,
      es_publico
    } = req.body;
  
    const { data, error } = await supabase
      .from("tableros")
      .update({
        nombre,
        color,
        icono,
        es_publico
      })
      .eq("id_tablero", id);
  
    res.json({ data, error });
  
  };

  const eliminarTablero = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("tableros")
      .delete()
      .eq("id_tablero", id);
  
    res.json({ data, error });
  
  };

  module.exports = {
    obtenerTableros,
    crearTablero,
    obtenerTableroPorId,
    actualizarTablero,
    eliminarTablero
  };