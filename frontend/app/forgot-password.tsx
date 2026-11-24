
import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Alert,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { router } from "expo-router";
import { forgotPassword } from "../services/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleRecovery = async () => {
    if (!email.trim()) {
      Alert.alert("Error", "Ingresá tu email");
      return;
    }

    try {
      setLoading(true);

      const resultado = await forgotPassword(email.trim());
      const data = resultado?.data;

      if (data?.reset_token) {
        router.push({
          pathname: "/reset-password",
          params: { token: data.reset_token },
        });
      } else {
        Alert.alert(
          "Solicitud enviada",
          data?.mensaje ||
            "Si el email existe, se generó un token de recuperación."
        );
      }
    } catch (error: any) {
      console.log("ERROR RECUPERACIÓN:", error?.response?.data);

      Alert.alert(
        "Error",
        error?.response?.data?.error ||
          "No se pudo solicitar la recuperación."
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
          paddingBottom: 60,
        }}
      >
        <TouchableOpacity onPress={() => router.back()}>
          <Ionicons name="arrow-back" size={25} color="white" />
        </TouchableOpacity>

        <Text
          style={{
            fontSize: 34,
            fontWeight: "bold",
            color: "white",
            marginTop: 35,
          }}
        >
          Recuperá tu contraseña
        </Text>

        <Text
          style={{
            color: "white",
            fontSize: 16,
            marginTop: 15,
          }}
        >
          Ingresá tu email para solicitar la recuperación de tu cuenta.
        </Text>
      </View>

      <View style={{ padding: 30, paddingTop: 40 }}>
        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          placeholderTextColor="#78909A"
          autoCapitalize="none"
          keyboardType="email-address"
          style={{
            backgroundColor: "#F1F6F8",
            padding: 18,
            borderRadius: 16,
            fontSize: 16,
            marginBottom: 25,
          }}
        />

        <TouchableOpacity
          onPress={handleRecovery}
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
            {loading ? "Enviando..." : "Enviar recuperación"}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}
