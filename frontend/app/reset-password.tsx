
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { resetPassword } from "../services/api";

export default function ResetPassword() {
  const { token: tokenParam } = useLocalSearchParams<{
    token?: string;
  }>();

  const [token, setToken] = useState(tokenParam || "");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleReset = async () => {
    if (!token.trim()) {
      Alert.alert("Error", "Ingresá el token de recuperación.");
      return;
    }

    if (password.length < 8) {
      Alert.alert(
        "Error",
        "La contraseña debe tener al menos 8 caracteres."
      );
      return;
    }

    if (!/[A-Z]/.test(password)) {
      Alert.alert(
        "Error",
        "La contraseña debe contener al menos una mayúscula."
      );
      return;
    }

    if (!/[^A-Za-z0-9]/.test(password)) {
      Alert.alert(
        "Error",
        "La contraseña debe contener al menos un carácter especial."
      );
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert("Error", "Las contraseñas no coinciden.");
      return;
    }

    try {
      setLoading(true);

      const resultado = await resetPassword(token.trim(), password);

      Alert.alert(
        "¡Listo!",
        resultado?.data?.mensaje ||
          "Tu contraseña se actualizó correctamente.",
        [
          {
            text: "Ir al login",
            onPress: () => router.replace("/login"),
          },
        ]
      );
    } catch (error: any) {
      console.log("ERROR CAMBIANDO CONTRASEÑA:", error?.response?.data);

      Alert.alert(
        "Error",
        error?.response?.data?.error ||
          "No se pudo actualizar la contraseña. Revisá el token."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={{ flex: 1, backgroundColor: "#FFFFFF" }}>
      <View
        style={{
          backgroundColor: "#356071",
          paddingHorizontal: 30,
          paddingTop: 100,
          paddingBottom: 55,
        }}
      >
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={{ color: "white", fontSize: 18 }}>← Volver</Text>
        </TouchableOpacity>

        <Text
          style={{
            fontSize: 34,
            fontWeight: "bold",
            color: "white",
            marginTop: 35,
          }}
        >
          Nueva contraseña
        </Text>

        <Text
          style={{
            color: "white",
            fontSize: 16,
            marginTop: 15,
          }}
        >
          Ingresá el token y elegí tu nueva contraseña.
        </Text>
      </View>

      <View style={{ padding: 30, paddingTop: 35 }}>
        <TextInput
          placeholder="Token de recuperación"
          value={token}
          onChangeText={setToken}
          autoCapitalize="none"
          placeholderTextColor="#78909A"
          style={inputStyle}
        />

        <TextInput
          placeholder="Nueva contraseña"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          placeholderTextColor="#78909A"
          style={inputStyle}
        />

        <TextInput
          placeholder="Confirmar contraseña"
          value={confirmPassword}
          onChangeText={setConfirmPassword}
          secureTextEntry
          placeholderTextColor="#78909A"
          style={inputStyle}
        />

        <Text
          style={{
            color: "#78909A",
            fontSize: 13,
            marginBottom: 25,
          }}
        >
          Mínimo 8 caracteres, una mayúscula y un carácter especial.
        </Text>

        <TouchableOpacity
          onPress={handleReset}
          disabled={loading}
          style={{
            backgroundColor: "#356071",
            padding: 20,
            borderRadius: 18,
            alignItems: "center",
            opacity: loading ? 0.7 : 1,
          }}
        >
          <Text
            style={{
              color: "white",
              fontWeight: "bold",
              fontSize: 18,
            }}
          >
            {loading ? "Actualizando..." : "Cambiar contraseña"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const inputStyle = {
  backgroundColor: "#F1F6F8",
  padding: 18,
  borderRadius: 16,
  fontSize: 16,
  marginBottom: 18,
  color: "#263238",
};
