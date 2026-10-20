
const multer = require("multer");

const storage = multer.memoryStorage();

const tiposPermitidos = {
  jpg: ["image/jpeg", "image/pjpeg"],
  jpeg: ["image/jpeg", "image/pjpeg"],
  jfif: ["image/jpeg", "image/pjpeg"],
  png: ["image/png"],
  webp: ["image/webp"]
};

const fileFilter = (req, file, callback) => {
  const extension = String(file.originalname || "")
    .split(".")
    .pop()
    .toLowerCase();

  const mimesValidos = tiposPermitidos[extension];

  if (
    mimesValidos &&
    mimesValidos.includes(file.mimetype)
  ) {
    return callback(null, true);
  }

  return callback(
    new Error(
      "Solo se permiten imágenes JPG, JPEG, JFIF, PNG o WEBP"
    )
  );
};

const upload = multer({
  storage,
  fileFilter,
  limits: {
    fileSize: 2 * 1024 * 1024,
    files: 1
  }
});

module.exports = upload;
