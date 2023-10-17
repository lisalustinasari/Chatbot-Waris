export const useSocketIO = () => {
  const socket = io(import.meta.env.VITE_SOCKETIO_HOST + '/chats');
  return {socket}
}