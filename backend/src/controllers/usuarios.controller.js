const supabase = require("../config/Supabase");

const obtenerUsuarios = async (req, res) => {

  const { data, error } = await supabase
    .from("usuarios")
    .select("*");

  res.json({ data, error });

};

const crearUsuario = async (req, res) => {

  const {
    nombre,
    email,
    password,
    rol,
    foto_perfil,
    ultima_sincronizacion
  } = req.body;

  const { data, error } = await supabase
    .from("usuarios")
    .insert([
      {
        nombre,
        email,
        password,
        rol,
        foto_perfil,
        ultima_sincronizacion
      }
    ]);

  res.json({
    message: "Usuario creado correctamente",
    data,
    error
  });

};

const obtenerUsuarioPorId = async (req, res) => {

  const { id } = req.params;

  const { data, error } = await supabase
    .from("usuarios")
    .select("*")
    .eq("id_usuario", id)
    .single();

  res.json({ data, error });
};

const actualizarUsuario = async (req, res) => {

  const { id } = req.params;

  const {
    nombre,
    email,
    password,
    rol,
    foto_perfil,
    ultima_sincronizacion
  } = req.body;

  const { data, error } = await supabase
    .from("usuarios")
    .update({
      nombre,
      email,
      password,
      rol,
      foto_perfil,
      ultima_sincronizacion
    })
    .eq("id_usuario", id);

  res.json({ data, error });
};

const eliminarUsuario = async (req, res) => {

  const { id } = req.params;

  const { data, error } = await supabase
    .from("usuarios")
    .delete()
    .eq("id_usuario", id);

  res.json({ data, error });
};

module.exports = {
  obtenerUsuarios,
  crearUsuario,
  obtenerUsuarioPorId,
  actualizarUsuario,
  eliminarUsuario
};