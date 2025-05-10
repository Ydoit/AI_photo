import { useEffect, useState } from "react"
import axios from "axios"

function App() {
  const [message, setMessage] = useState("")

  useEffect(() => {
    axios.get("http://localhost:8000").then(res => {
      setMessage(res.data.message)
    })
  }, [])

  return (
    <div className="p-6 text-xl text-blue-600">
      <h1>图片管理工具</h1>
      <p>后端状态：{message}</p>
    </div>
  )
}

export default App
