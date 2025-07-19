using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;

public class UDPHandGestureReceiver : MonoBehaviour
{
    UdpClient udpClient;
    Thread receiveThread;
    volatile bool running = true;
    string lastGesture = "";

    void Start()
    {
        udpClient = new UdpClient(65432); // 和 Python 一致
        receiveThread = new Thread(ReceiveData);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveData()
    {
        while (running)
        {
            IPEndPoint remoteEndPoint = new IPEndPoint(IPAddress.Any, 0);
            byte[] data = udpClient.Receive(ref remoteEndPoint);
            string message = Encoding.ASCII.GetString(data);
            Debug.Log("收到手勢: " + message);

            lastGesture = message;

            // 可根據不同手勢做不同反應
            if (message == "OK")
            {
                // 觸發 OK 動作
            }
            else if (message == "YA")
            {
                // 觸發 YA 動作
            }
            else if (message == "OPEN")
            {
                // 觸發 張開手 動作
            }
            else if (message == "THUMB_RIGHT")
            {
                // 觸發 拇指右 動作
            }
        }
    }

    void OnDestroy()
    {
        running = false;
        udpClient.Close();
        if (receiveThread != null) receiveThread.Abort();
    }

    void Update()
    {
        // 你可以在這裡用 lastGesture 控制場景角色、動畫等
    }
}
