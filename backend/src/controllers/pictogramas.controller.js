const supabase = require("../config/Supabase");

const obtenerPictogramas = async (req, res) => {

  const { data, error } = await supabase
    .from("pictogramas")
    .select("*");

  res.json({ data, error });

};

const crearPictograma = async (req, res) => {

    const {
      id_categorias,
      nombre,
      imagen_url,
      audio_url,
      es_personalizado
    } = req.body;
  
    const { data, error } = await supabase
      .from("pictogramas")
      .insert([
        {
          id_categorias,
          nombre,
          imagen_url,
          audio_url,
          es_personalizado
        }
      ])
      .select();
  
    res.json({
      data,
      error
    });
  
  };

  const obtenerPictogramaPorId = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("pictogramas")
      .select("*")
      .eq("id_pictogramas", id)
      .single();
  
    res.json({
      data,
      error
    });
  
  };

  const actualizarPictograma = async (req, res) => {

    const { id } = req.params;
  
    const {
      nombre,
      imagen_url,
      audio_url,
      es_personalizado
    } = req.body;
  
    const { data, error } = await supabase
      .from("pictogramas")
      .update({
        nombre,
        imagen_url,
        audio_url,
        es_personalizado
      })
      .eq("id_pictogramas", id);
  
    res.json({
      data,
      error
    });
  
  };

  const eliminarPictograma = async (req, res) => {

    const { id } = req.params;
  
    const { data, error } = await supabase
      .from("pictogramas")
      .delete()
      .eq("id_pictogramas", id);
  
    res.json({
      data,
      error
    });
  
  };

  const obtenerPictogramasPorCategoria = async (req, res) => {

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

const obtenerPictogramasPersonalizados = async (req, res) => {

  const { data, error } = await supabase
    .from("pictogramas")
    .select("*")
    .eq("es_personalizado", true);

  res.json({
    data,
    error
  });

};

  module.exports = {
    obtenerPictogramas,
    crearPictograma,
    obtenerPictogramaPorId,
    actualizarPictograma,
    eliminarPictograma,
    obtenerPictogramasPorCategoria,
    obtenerPictogramasPersonalizados
  };