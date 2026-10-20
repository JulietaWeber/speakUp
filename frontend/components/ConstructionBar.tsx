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
    if (palabras.length === 0 || seleccionada) return;

    setSeleccionada(true);

    // La oración completa incluye pictogramas y palabras sugeridas por IA.
    const textoCompleto = palabras
      .map((palabra) => palabra.nombre)
      .filter((nombre) => typeof nombre === "string" && nombre.trim().length > 0)
      .join(" ");

    // El backend de armarFrase necesita IDs reales. Las sugerencias de IA
    // son texto libre, por eso no se envían como IDs de pictogramas.
    const idsPictogramas = palabras
      .filter((p: any) => p.id_pictogramas !== null && p.id_pictogramas !== undefined)
      .map((p: any) => p.id_pictogramas);

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

    if (!textoCompleto.trim()) {
      setSeleccionada(false);
      return;
    }

    try {
      if (idsPictogramas.length === 0) {
        console.log("La oración no contiene pictogramas guardados para crear el registro.");
        setSeleccionada(false);
        return;
      }

      const respuesta = await armarFrase(
        usuario.id_usuario,
        idsPictogramas,
        token
      );

      console.log("=================================");
      console.log("FRASE CREADA:");
      console.log("Texto completo que se va a reproducir:", textoCompleto);
      console.log(respuesta);
      console.log("=================================");

      // Importante: enviar el texto completo, no solo el texto que devuelve
      // armarFrase basado en los pictogramas guardados.
      const audio = await generarAudio(
        respuesta.id_frase,
        textoCompleto,
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
      <View style={styles.topRow}>
        <TouchableOpacity
          activeOpacity={0.7}
          onPress={confirmarOracion}
          disabled={palabras.length === 0 || seleccionada}
          style={[
            styles.playButton,
            (palabras.length === 0 || seleccionada) && styles.playButtonDisabled,
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
            <Ionicons name="trash-outline" size={22} color="#6F7C80" />
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
