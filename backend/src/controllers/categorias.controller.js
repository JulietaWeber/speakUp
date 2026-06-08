const supabase = require("../config/Supabase");

const obtenerCategorias = async (req, res) => {

  const { data, error } = await supabase
    .from("categorias")
    .select("*");

  res.json({ data, error });

};

const crearCategoria = async (req, res) => {

  const {
    nombre,
    color
  } = req.body;

  const { data, error } = await supabase
    .from("categorias")
    .insert([
      {
        nombre,
        color
      }
    ])
    .select();

  res.json({
    data,
    error
  });

};

const obtenerCategoriaPorId = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("categorias")
      .select("*")
      .eq("id_categorias", id)
      .single();
  
    res.json({
      data,
      error
    });
  
  };

  const actualizarCategoria = async (req, res) => {

    const { id } = req.params;
  
    const {
      nombre,
      color
    } = req.body;
  
    const { data, error } = await supabase
      .from("categorias")
      .update({
        nombre,
        color
      })
      .eq("id_categorias", id);
  
    res.json({
      data,
      error
    });
  
  };

  const eliminarCategoria = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("categorias")
      .delete()
      .eq("id_categorias", id);
  
    res.json({
      data,
      error
    });
  
  };

  const obtenerPictogramasDeCategoria = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("pictogramas")
      .select("*")
      .eq("id_categorias", id);
  
    res.json({
      data,
      error
    });
  
  };

  module.exports = {
    obtenerCategorias,
    crearCategoria,
    obtenerCategoriaPorId,
    actualizarCategoria,
    eliminarCategoria,
    obtenerPictogramasDeCategoria
  };