import static javax.swing.UIManager.get;
import static javax.swing.UIManager.getDefaults;
import static javax.swing.UIManager.put;

import java.awt.Font;
import java.util.Enumeration;

import javax.swing.plaf.FontUIResource;

import pipe.gui.CreateGui;

/**
 * -@author Qi Mo
 * ����pipe2.5��ģ����֯���̵�Petri��(�漰ͬ��,�첽,��Դ��ʱ��)
 */

public class RunGui {

    public static void main(String args[]) {
        // ����������Ϊ����ƻ��"PingFang SC"
        InitGlobalFont(new Font("PingFang SC", Font.PLAIN, 12));
        CreateGui.init();
    }

    // ͳһ��������
    private static void InitGlobalFont(Font font) {
        FontUIResource fontRes = new FontUIResource(font);
        for (Enumeration<Object> keys = getDefaults().keys(); keys.hasMoreElements();) {
            Object key = keys.nextElement();
            Object value = get(key);
            if (value instanceof FontUIResource) {
                put(key, fontRes);
            }
        }
    }
}
