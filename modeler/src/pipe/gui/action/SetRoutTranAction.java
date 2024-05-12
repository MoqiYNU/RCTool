package pipe.gui.action;

import java.awt.Container;
import java.awt.event.ActionEvent;

import javax.swing.AbstractAction;

import pipe.dataLayer.Transition;
import pipe.gui.CreateGui;

@SuppressWarnings("serial")
public class SetRoutTranAction extends AbstractAction{

	 @SuppressWarnings("unused")
	 private Container contentPane;
	 private Transition selected;


	 public SetRoutTranAction(Container contentPane, Transition transition) {
	    this.contentPane = contentPane;
	    selected = transition;
	 }
	
	@Override
	public void actionPerformed(ActionEvent e) {
		
		//����selectedΪ·�ɱ�Ǩ
		selected.setRoutTran(true);
		//���ѡ���Ǩ��Id
		CreateGui.getModel().addRoutTran(selected.getId());
		//�ػ浱ǰ����
		selected.repaint();
		
	}

 }
