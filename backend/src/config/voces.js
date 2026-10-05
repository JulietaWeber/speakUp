const VOCES_DISPONIBLES = {
  voz_neutra: {
    id: "voz_neutra",
    nombre: "Voz neutra",
    descripcion: "Voz clara para uso general",
    voice_id: process.env.ELEVENLABS_VOICE_ID
  },

  voz_femenina: {
    id: "voz_femenina",
    nombre: "Voz femenina",
    descripcion: "Voz femenina clara y suave",
    voice_id: process.env.ELEVENLABS_VOICE_ID_FEMENINA
  },

  voz_masculina: {
    id: "voz_masculina",
    nombre: "Voz masculina",
    descripcion: "Voz masculina clara",
    voice_id: process.env.ELEVENLABS_VOICE_ID_MASCULINA
  },

  voz_infantil: {
    id: "voz_infantil",
    nombre: "Voz juvenil",
    descripcion: "Voz más liviana y expresiva",
    voice_id: process.env.ELEVENLABS_VOICE_ID_INFANTIL
  },

  voz_suave: {
    id: "voz_suave",
    nombre: "Voz suave",
    descripcion: "Voz pausada y tranquila",
    voice_id: process.env.ELEVENLABS_VOICE_ID_SUAVE
  }
};

const VOZ_DEFAULT = "voz_neutra";

const obtenerVocesPublicas = () => {
  return Object.values(VOCES_DISPONIBLES).map((voz) => ({
    id: voz.id,
    nombre: voz.nombre,
    descripcion: voz.descripcion
  }));
};

const obtenerVoiceIdPorVoz = (vozPreferida) => {
  const voz = VOCES_DISPONIBLES[vozPreferida] || VOCES_DISPONIBLES[VOZ_DEFAULT];

  return voz.voice_id || process.env.ELEVENLABS_VOICE_ID;
};

const existeVoz = (vozPreferida) => {
  return Boolean(VOCES_DISPONIBLES[vozPreferida]);
};

module.exports = {
  VOCES_DISPONIBLES,
  VOZ_DEFAULT,
  obtenerVocesPublicas,
  obtenerVoiceIdPorVoz,
  existeVoz
};