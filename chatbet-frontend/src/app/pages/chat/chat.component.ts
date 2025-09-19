import { Component } from '@angular/core';
import { ChatInterfaceComponent } from '../../components/chat-interface/chat-interface.component';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [
    ChatInterfaceComponent
  ],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent {

}
