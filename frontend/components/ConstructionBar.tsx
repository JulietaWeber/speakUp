import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAudioPlayer, setAudioModeAsync } from "expo-audio";
import { useConstruction } from "../context/ConstructionContext";
import { armarFrase, generarAudio } from "../services/api";

export default function ConstructionBar() {
  const { palabras, borrarUltimaPalabra, limpiar } = useConstruction();
  const [seleccionada, setSeleccionada] = useState(false);

  const player = useAudioPlayer(null);

  useEffect(() => {
    setAudioModeAsync({
      playsInSilentMode: true,
      shouldPlayInBackground: false,
    }).catch((error) => {
      console.log("ERROR CONFIGURANDO AUDIO:", error);
    });
  }, []);

  useEffect(() => {
    setSeleccionada(false);
  }, [palabras]);

  const reproducirAudio = (audioUrl: string) => {
    try {
      console.log("REPRODUCIENDO AUDIO:");
      console.log(audioUrl);

      player.replace(audioUrl);
      player.volume = 1;
      player.play();

      console.log("AUDIO REPRODUCIÉNDOSE");
    } catch (error) {
      console.log("ERROR REPRODUCIENDO AUDIO:", error);
    }
  };

  const confirmarOracion = async () => {
    if (palabras.length === 0) return;

    setSeleccionada(true);

    const idsPictogramas = palabras.map(
      (p) => p.id_pictogramas
    );

    const token = await AsyncStorage.getItem("token");
    const usuarioGuardado = await AsyncStorage.getItem("usuario");

    const usuario = usuarioGuardado
      ? JSON.parse(usuarioGuardado)
      : null;

    if (!usuario || !token) {
      console.log("No hay sesión iniciada");
      setSeleccionada(false);
      return;
    }

    try {
      const respuesta = await armarFrase(
        usuario.id_usuario,
        idsPictogramas,
        token
      );

      console.log("=================================");
      console.log("FRASE CREADA:");
      console.log(respuesta);
      console.log("=================================");

      const audio = await generarAudio(
        respuesta.id_frase,
        respuesta.texto,
        token
      );

      console.log("=================================");
      console.log("AUDIO GENERADO:");
      console.log(audio);
      console.log("=================================");

      if (audio?.audio_url) {
        reproducirAudio(audio.audio_url);
      }
    } catch (error) {
      console.log(
        "Error enviando frase, generando audio o reproduciendo:",
        error
      );
    } finally {
      setSeleccionada(false);
    }
  };

  return (
    <View
      style={[
        styles.container,
        seleccionada && styles.containerSeleccionado,
      ]}
    >
      <TouchableOpacity
        activeOpacity={1}
        onPress={confirmarOracion}
        style={styles.wordsArea}
      >
        <View style={styles.topRow}>
          <View style={styles.wordsContainer}>
            {palabras.length === 0 ? (
              <Text style={styles.placeholderText}>
                Selecciona tus palabras para poder reproducir tu frase.
              </Text>
            ) : (
              <Text style={styles.text}>
                {palabras.map((p) => p.nombre).join(" ")}
              </Text>
            )}
          </View>

          {palabras.length > 0 && (
            <TouchableOpacity
              onPress={borrarUltimaPalabra}
              style={styles.deleteButton}
            >
              <Text style={styles.deleteText}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </TouchableOpacity>

      {palabras.length > 0 && (
        <TouchableOpacity
          onPress={limpiar}
          style={styles.clearButton}
        >
          <Text style={styles.clearText}>
            Reiniciar oración
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    padding: 10,
    borderRadius: 15,
    marginBottom: 20,
    elevation: 3,
  },

  containerSeleccionado: {
    backgroundColor: "#BDBDBD",
  },

  wordsArea: {
    width: "100%",
  },

  topRow: {
    flexDirection: "row",
    alignItems: "center",
  },

  wordsContainer: {
    flex: 1,
    justifyContent: "center",
    minHeight: 45,
  },

  placeholderText: {
    fontSize: 14,
    color: "#8A969A",
    textAlign: "center",
    paddingHorizontal: 8,
  },

  text: {
    fontSize: 22,
    color: "#356879",
  },

  deleteButton: {
    width: 40,
    height: 40,
    backgroundColor: "#8C8C8C",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 8,
    marginLeft: 10,
  },

  deleteText: {
    color: "#FFFFFF",
    fontSize: 24,
    fontWeight: "bold",
  },

  clearButton: {
    marginTop: 15,
    backgroundColor: "#EF4444",
    borderRadius: 10,
    padding: 10,
    alignItems: "center",
  },

  clearText: {
    color: "#FFFFFF",
    fontWeight: "bold",
    fontSize: 16,
  },
});