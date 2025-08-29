package U12_20;

public class Demo {
	public static void main(String [] args) {
		SaleTicket mt = new SaleTicket(); 
		Thread t1 = new Thread(mt, "1号窗口"); 
		Thread t2 = new Thread(mt, "2号窗口"); 
		Thread t3 = new Thread(mt, "3号窗口"); 
		t1.start();
		t2.start();
		t3.start();
	}
}