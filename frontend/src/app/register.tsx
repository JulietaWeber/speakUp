import {
    View,
    Text,
    TextInput,
    TouchableOpacity,
  } from "react-native";
  
  import { router } from "expo-router";
  
  export default function Register() {
    return (
      <View
        style={{
          flex: 1,
          backgroundColor: "#f4f7fb",
          justifyContent: "center",
          paddingHorizontal: 30,
        }}
      >
        <Text
          style={{
            fontSize: 38,
            fontWeight: "bold",
            color: "#219ebc",
            textAlign: "center",
            marginBottom: 40,
          }}
        >
          Crear Cuenta
        </Text>
  
        <TextInput
          placeholder="Nombre"
          style={{
            backgroundColor: "white",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
          }}
        />
  
        <TextInput
          placeholder="Email"
          style={{
            backgroundColor: "white",
            padding: 18,
            borderRadius: 16,
            marginBottom: 20,
          }}
        />
  
        <TextInput
          placeholder="Contraseña"
          secureTextEntry
          style={{
            backgroundColor: "white",
            padding: 18,
            borderRadius: 16,
            marginBottom: 30,
          }}
        />
  
        <TouchableOpacity
          onPress={() => router.push("/categories")}
          style={{
            backgroundColor: "#219ebc",
            padding: 20,
            borderRadius: 18,
            alignItems: "center",
          }}
        >
          <Text
            style={{
              color: "white",
              fontWeight: "bold",
              fontSize: 18,
            }}
          >
            Registrarse
          </Text>
        </TouchableOpacity>
  
        <TouchableOpacity
          onPress={() => router.push("/login")}
          style={{
            marginTop: 20,
          }}
        >
          <Text
            style={{
              textAlign: "center",
              color: "#219ebc",
            }}
          >
            Ya tengo cuenta
          </Text>
        </TouchableOpacity>
      </View>
    );
  }