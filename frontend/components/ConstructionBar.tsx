
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useState, useEffect } from "react";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useAudioPlayer, setAudioModeAsync } from "expo-audio";
import { useConstruction } from "../context/ConstructionContext";
import { armarFrase, generarAudio } from "../services/api";

export default function ConstructionBar() {
  const { palabras, borrarUltimaPalabra } = useConstruction();
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
      console.log("REPRODUCIENDO AUDIO:", audioUrl);
      player.replace(audioUrl);
      player.volume = 1;
      player.play();
    } catch (error) {
      console.log("ERROR REPRODUCIENDO AUDIO:", error);
    }
  };

  const confirmarOracion = async () => {
    if (palabras.length === 0 || seleccionada) return;

    setSeleccionada(true);

    try {
      const palabrasTexto = palabras
        .map((palabra) => palabra.nombre)
        .filter(
          (nombre) =>
            typeof nombre === "string" && nombre.trim().length > 0
        );

      const textoCompleto = palabrasTexto.join(" ").trim();

      const idsPictogramas = palabras.flatMap((palabra: any) => {
        if (Array.isArray(palabra.ids_pictogramas_origen)) {
          return palabra.ids_pictogramas_origen;
        }

        if (
          palabra.id_pictogramas !== null &&
          palabra.id_pictogramas !== undefined
        ) {
          return [palabra.id_pictogramas];
        }

        return [];
      });

      const token = await AsyncStorage.getItem("token");
      const usuarioGuardado = await AsyncStorage.getItem("usuario");

      const usuario = usuarioGuardado
        ? JSON.parse(usuarioGuardado)
        : null;

      if (!usuario || !token) {
        console.log("No hay sesión iniciada");
        return;
      }

      if (!textoCompleto) return;

      if (idsPictogramas.length === 0) {
        console.log(
          "La oración no contiene pictogramas guardados para crear el registro."
        );
        return;
      }

      const respuesta = await armarFrase(
        usuario.id_usuario,
        [...new Set(idsPictogramas)],
        token
      );

      console.log("FRASE CREADA:", respuesta);

      const audio = await generarAudio(
        respuesta.id_frase,
        textoCompleto,
        token
      );

      console.log("AUDIO GENERADO:", audio);

      if (audio?.audio_url) {
        reproducirAudio(audio.audio_url);
      }
    } catch (error: any) {
      console.log(
        "ERROR EN LA FRASE O EN LA GENERACIÓN DEL AUDIO:",
        error?.response?.data ?? error?.message ?? error
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
      <View style={styles.topRow}>
        <TouchableOpacity
          activeOpacity={0.7}
          onPress={confirmarOracion}
          disabled={palabras.length === 0 || seleccionada}
          style={[
            styles.playButton,
            (palabras.length === 0 || seleccionada) &&
              styles.playButtonDisabled,
          ]}
          accessibilityLabel="Reproducir oración completa"
        >
          <Ionicons name="play" size={23} color="#FFFFFF" />
        </TouchableOpacity>

        <View style={styles.wordsContainer}>
          {palabras.length === 0 ? (
            <Text style={styles.placeholderText}>
              Seleccioná tus palabras para reproducir tu frase.
            </Text>
          ) : (
            <Text style={styles.text}>
              {palabras.map((p) => p.nombre).join(" ")}
            </Text>
          )}
        </View>

        {palabras.length > 0 && (
          <TouchableOpacity
            activeOpacity={0.7}
            onPress={borrarUltimaPalabra}
            style={styles.deleteButton}
            accessibilityLabel="Borrar última palabra"
          >
            <Ionicons
              name="trash-outline"
              size={22}
              color="#6F7C80"
            />
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    paddingHorizontal: 12,
    paddingVertical: 12,
    borderRadius: 16,
    marginBottom: 14,
    elevation: 2,
    borderWidth: 1,
    borderColor: "#E2EAED",
    minHeight: 70,
    justifyContent: "center",
  },

  containerSeleccionado: {
    borderColor: "#356879",
  },

  topRow: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 48,
    gap: 12,
  },

  playButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#356879",
    justifyContent: "center",
    alignItems: "center",
  },

  playButtonDisabled: {
    opacity: 0.85,
  },

  wordsContainer: {
    flex: 1,
    justifyContent: "center",
    minHeight: 48,
    paddingVertical: 4,
  },

  placeholderText: {
    fontSize: 12,
    color: "#8A969A",
    textAlign: "center",
    paddingHorizontal: 4,
  },

  text: {
    fontSize: 16,
    color: "#356879",
  },

  deleteButton: {
    width: 40,
    height: 40,
    backgroundColor: "#F1F5F6",
    justifyContent: "center",
    alignItems: "center",
    borderRadius: 10,
    marginLeft: 2,
  },
});
