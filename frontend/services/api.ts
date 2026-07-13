import axios from "axios";

const API_URL = process.env.EXPO_PUBLIC_API_URL!;

export type Pictograma = {
  id_pictogramas: number;
  id_categorias: number;
  nombre: string;
  imagen_url: string | null;
  audio_url: string | null;
  es_personalizado?: boolean;
};

export const obtenerCategorias = async () => {
  const response = await axios.get(`${API_URL}/categorias`);
  return response.data.data;
};

export const obtenerPictogramas = async (): Promise<Pictograma[]> => {
  const response = await axios.get(`${API_URL}/pictogramas`);
  return response.data.data;
};

export const obtenerPictogramasPorCategoria = async (
  idCategoria: number
): Promise<Pictograma[]> => {
  const response = await axios.get(
    `${API_URL}/pictogramas/categoria/${idCategoria}`
  );

  return response.data.data;
};

export const armarFrase = async (
  idUsuario: number,
  pictogramas: number[],
  token: string
) => {
  const response = await axios.post(
    `${API_URL}/frases/armar`,
    {
      id_usuario: idUsuario,
      pictogramas,
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data.data;
};

export const login = async (email: string, password: string) => {
  const response = await axios.post(`${API_URL}/auth/login`, {
    email,
    password,
  });

  return response.data.data;
};

export const register = async (
  nombre: string,
  email: string,
  password: string
) => {
  const response = await axios.post(`${API_URL}/auth/register`, {
    nombre,
    email,
    password,
  });

  return response.data.data;
};