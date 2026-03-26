type FileItem = {
  file: string;
  sender: string;
  status: string;
};

type Props = {
  fileData: FileItem;
  onDecrypt: (file: string) => void;
  loading: boolean;
};

export default function FileCard({ fileData, onDecrypt, loading }: Props) {
  const { file, sender, status } = fileData;

  return (
    <div className="bg-gray-800 hover:bg-gray-700 transition p-5 rounded-xl border border-gray-700 flex justify-between items-center shadow hover:shadow-lg">
      
      {/* LEFT SIDE */}
      <div>
        <p className="text-lg font-semibold">{file}</p>
        <p className="text-sm text-gray-400">{sender}</p>

        <div className="mt-2 flex gap-2">
          {/* STATUS */}
          <span
            className={`text-xs px-2 py-1 rounded ${
              status === "sent"
                ? "bg-yellow-600"
                : "bg-green-600"
            }`}
          >
            {status}
          </span>

          {/* SECURITY TAG */}
          <span className="text-xs px-2 py-1 rounded bg-blue-600">
            Encrypted
          </span>
        </div>
      </div>

      {/* RIGHT SIDE */}
      <button
        onClick={() => onDecrypt(file)}
        disabled={loading}
        className="bg-green-600 px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? "Decrypting..." : "Decrypt"}
      </button>
    </div>
  );
}