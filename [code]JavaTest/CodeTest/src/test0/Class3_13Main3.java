package test0;
import java.util.Scanner;
public class Class3_13Main3 {

	public static void main(String[] args) {
		Scanner input;
		input=new Scanner(System.in);
		// hasNext()的应用
		
		while(input.hasNext()) {
			int p=input.nextInt();
			double k=p*0.454;
			System.out.println(k);
		}
	}

}
