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
import { register } from "../services/api";

export default function Register() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim()) {
      Alert.alert("Error", "Ingresá tu nombre");
      return;
    }

    if (!email.trim()) {
      Alert.alert("Error", "Ingresá tu email");
      return;
    }

    if (!password.trim()) {
      Alert.alert("Error", "Ingresá una contraseña");
      return;
    }

    try {
      setLoading(true);

      const data = await register(name, email, password);

      console.log("Usuario registrado:", data);

      Alert.alert(
        "Éxito",
        "Usuario registrado correctamente."
      );

      router.replace("/login");
    } catch (error: any) {
      console.log("ERROR REGISTER:");
      console.log(error);
      console.log(error.response);
      console.log(error.response?.data);

      Alert.alert(
        "Error",
        JSON.stringify(error.response?.data || error.message)
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <View
      style={{
        flex: 1,
        backgroundColor: "#356071",
      }}
    >
      {/* TÍTULO CENTRADO ARRIBA */}
      <View
        style={{
          alignItems: "center",
          paddingHorizontal: 30,
          paddingTop: 150,
          paddingBottom: 120,
          backgroundColor: "#356071",
        }}
      >
        <Text
          style={{
            fontSize: 38,
            fontWeight: "bold",
            color: "white",
            textAlign: "center",
          }}
        >
          Crea una cuenta
        </Text>
      </View>

      {/* CONTAINER CELESTE DESDE GOOGLE HACIA ABAJO */}
      <View
        style={{
          flex: 1,
          backgroundColor: "#AFD4E8",
          borderTopLeftRadius: 30,
          borderTopRightRadius: 30,
          paddingHorizontal: 30,
          paddingTop: 25,
          overflow: "hidden",
        }}
      >
        {/* BOTÓN DE GOOGLE */}
        <TouchableOpacity
          style={{
            backgroundColor: "#CFE6F1",
            padding: 18,
            borderRadius: 16,
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <View
            style={{
              flexDirection: "row",
              alignItems: "center",
            }}
          >
            <Ionicons
              name="logo-google"
              size={18}
              color="#356071"
            />

            <Text
              style={{
                color: "#356071",
                fontWeight: "bold",
                marginLeft: 10,
              }}
            >
              Continuar con Google
            </Text>
          </View>
        </TouchableOpacity>

        {/* SEPARACIÓN CON LA "O" */}
        <View
          style={{
            flexDirection: "row",
            alignItems: "center",
            marginBottom: 20,
          }}
        >
          <View
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "#356071",
            }}
          />

          <Text
            style={{
              color: "#356071",
              marginHorizontal: 12,
              fontSize: 14,
              fontWeight: "bold",
            }}
          >
            o
          </Text>

          <View
            style={{
              flex: 1,
              height: 1,
              backgroundColor: "#356071",
            }}
          />
        </View>

        {/* NOMBRE */}
        <TextInput
          placeholder="Nombre"
          value={name}
          onChangeText={setName}
          placeholderTextColor="#356071"
          style={{
            backgroundColor: "#CFE6F1",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
          }}
        />

        {/* EMAIL */}
        <TextInput
          placeholder="Email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          placeholderTextColor="#356071"
          style={{
            backgroundColor: "#CFE6F1",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
          }}
        />

        {/* CONTRASEÑA + CUADRADO DEL OJO */}
        <View
          style={{
            flexDirection: "row",
            marginBottom: 30,
          }}
        >
          <TextInput
            placeholder="Contraseña"
            value={password}
            onChangeText={setPassword}
            secureTextEntry={!showPassword}
            placeholderTextColor="#356071"
            style={{
              flex: 1,
              backgroundColor: "#CFE6F1",
              padding: 18,
              borderTopLeftRadius: 16,
              borderBottomLeftRadius: 16,
              borderTopRightRadius: 0,
              borderBottomRightRadius: 0,
            }}
          />

          <TouchableOpacity
            onPress={() => setShowPassword(!showPassword)}
            style={{
              width: 50,
              backgroundColor: "#CFE6F1",
              borderLeftWidth: 5,
              borderLeftColor: "#AFD4E8",
              borderTopRightRadius: 16,
              borderBottomRightRadius: 16,
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Ionicons
              name={
                showPassword
                  ? "eye-outline"
                  : "eye-off-outline"
              }
              size={16}
              color="#356071"
            />
          </TouchableOpacity>
        </View>

        {/* BOTÓN CREAR CUENTA */}
        <TouchableOpacity
          onPress={handleRegister}
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
            {loading ? "Registrando..." : "Crear cuenta"}
          </Text>
        </TouchableOpacity>

        {/* INICIAR SESIÓN */}
        <TouchableOpacity
          onPress={() => router.push("/login")}
          style={{
            marginTop: 20,
          }}
        >
          <Text
            style={{
              textAlign: "center",
              color: "#356071",
            }}
          >
            Ya tenes una cuenta?{" "}
            <Text
              style={{
                textDecorationLine: "underline",
              }}
            >
              Inicia sesión
            </Text>
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}