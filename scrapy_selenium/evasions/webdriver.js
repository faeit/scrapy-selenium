const newProto = navigator.__proto__;
delete newProto.webdriver;
navigator.__proto__ = newProto;